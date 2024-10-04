from flask import Flask, jsonify, request, render_template
import json
import time
from threading import Thread
import random

app = Flask(__name__)  # Flask-App initialisieren

class Bank:
    def __init__(self, interest_rate_min=0.01, interest_rate_max=0.05, interval=300, data_file='bank_data.json'):
        self.accounts = {}
        self.account_history = {}
        self.interest_rate_min = interest_rate_min
        self.interest_rate_max = interest_rate_max
        self.interval = interval
        self.interest_history = []
        self.data_file = data_file
        self.load_data()

    # Intervall aktualisieren
    def update_interval(self, new_interval):
        self.interval = new_interval
        self.save_data() 

    def create_account(self, player_name):
        if player_name not in self.accounts:
            self.accounts[player_name] = 0
            self.account_history[player_name] = []
            return f"Konto für {player_name} erstellt."
        return f"{player_name} hat bereits ein Konto."

    def deposit(self, player_name, amount):
        if player_name in self.accounts:
            self.accounts[player_name] += amount
            self.account_history[player_name].append({
                "type": "Einzahlung",
                "amount": amount,
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            })
            return f"{amount} für {player_name} eingezahlt."
        return f"{player_name} hat kein Konto."

    def withdraw(self, player_name, amount):
        if player_name in self.accounts:
            if self.accounts[player_name] >= amount:
                self.accounts[player_name] -= amount
                self.account_history[player_name].append({
                    "type": "Auszahlung",
                    "amount": -amount,
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                })
                return f"{amount} von {player_name} abgezogen."
            return f"Nicht genügend Guthaben für die Auszahlung."
        return f"{player_name} hat kein Konto."

    def apply_random_interest(self):
        random_interest_rate = random.uniform(self.interest_rate_min, self.interest_rate_max)
        interest_data = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "rate": random_interest_rate,
            "accounts": {}
        }

        for player, balance in self.accounts.items():
            interest = balance * random_interest_rate
            self.accounts[player] += interest
            self.account_history[player].append({
                "type": "Zinsen",
                "amount": interest,
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            })
            interest_data["accounts"][player] = interest

        self.interest_history.append(interest_data)
        self.save_data()


    def save_data(self):
        data = {
            "accounts": self.accounts,
            "account_history": self.account_history,
            "interest_rate_min": self.interest_rate_min,
            "interest_rate_max": self.interest_rate_max,
            "interest_history": self.interest_history
        }
        with open(self.data_file, 'w') as file:
            json.dump(data, file, indent=4)

    def load_data(self):
        try:
            with open(self.data_file, 'r') as file:
                data = json.load(file)
                self.accounts = data.get("accounts", {})
                self.account_history = data.get("account_history", {})
                self.interest_rate_min = data.get("interest_rate_min", 0.01)
                self.interest_rate_max = data.get("interest_rate_max", 0.05)
                self.interest_history = data.get("interest_history", [])
        except FileNotFoundError:
            print(f"{self.data_file} nicht gefunden, starte mit neuen Daten.")



bank = Bank()

def interest_thread():
    while True:
        current_interval = bank.interval  # Aktuelles Intervall erfassen
        for _ in range(current_interval):
            time.sleep(1)  # Jede Sekunde warten und das Intervall dynamisch prüfen
            if current_interval != bank.interval:
                break  # Wenn sich das Intervall ändert, Schleife verlassen und neu starten
        bank.apply_random_interest()


thread = Thread(target=interest_thread)
thread.daemon = True
thread.start()

@app.route('/')
def index():
    return render_template('index.html', interest_history=bank.interest_history)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        min_rate = float(request.form['min_rate'])
        max_rate = float(request.form['max_rate'])
        bank.interest_rate_min = min_rate
        bank.interest_rate_max = max_rate
        bank.save_data()
        return jsonify({'message': 'Zinssatzbereich aktualisiert!'})
    return render_template('settings.html', min_rate=bank.interest_rate_min, max_rate=bank.interest_rate_max, interval=bank.interval)


@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        player_name = request.form['player_name']
        message = bank.create_account(player_name)
        bank.save_data()
        return jsonify({'message': message})
    return render_template('create_account.html')

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if request.method == 'POST':
        player_name = request.form['player_name']
        amount = float(request.form['amount'])
        message = bank.deposit(player_name, amount)
        bank.save_data()
        return jsonify({'message': message})
    return render_template('deposit.html')

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if request.method == 'POST':
        player_name = request.form['player_name']
        amount = float(request.form['amount'])
        message = bank.withdraw(player_name, amount)
        bank.save_data()
        return jsonify({'message': message})
    return render_template('withdraw.html')

@app.route('/accounts')
def get_accounts():
    return render_template('accounts.html', accounts=bank.accounts)

@app.route('/account/<player_name>')
def account_detail(player_name):
    if player_name in bank.accounts:
        account_history = bank.account_history.get(player_name, [])
        current_balance = bank.accounts.get(player_name, 0)  # Aktueller Kontostand
        return render_template('account_detail.html', player_name=player_name, account_history=account_history, current_balance=current_balance)
    else:
        return f"Konto für {player_name} nicht gefunden.", 404

@app.route('/get_interest_history', methods=['GET'])
def get_interest_history():
    return jsonify(bank.interest_history)

@app.route('/get_users', methods=['GET'])
def get_users():
    users = list(bank.accounts.keys())
    return jsonify(users)

@app.route('/reset_data', methods=['POST'])
def reset_data():
    bank.accounts = {}
    bank.account_history = {}
    bank.interest_history = []
    bank.interest_rate_min = 0.01
    bank.interest_rate_max = 0.05
    bank.save_data()  # Gespeicherte Daten zurücksetzen
    return jsonify({'message': 'Alle Daten wurden zurückgesetzt!'})

@app.route('/update_interval', methods=['POST'])
def update_interval():
    new_interval = int(request.form['interval'])  # Neues Intervall in Sekunden
    bank.update_interval(new_interval)
    return jsonify({'message': 'Intervall wurde erfolgreich aktualisiert!'})


if __name__ == '__main__':
    app.run(debug=True)
