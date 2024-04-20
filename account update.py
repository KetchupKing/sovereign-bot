import os
import json
import re

with open('data.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

accounts = {}

for line in lines:
    match = re.search(r'#\d+ - (.*?)(\'s account)? - ㏜ (\d{1,3}(?:,\d{3})*)', line)
    if match:
        username, _, balance = match.groups()
        balance = balance.replace(',', '')
        accounts[username] = int(balance)

not_found = []
for username, balance in accounts.items():
    for filename in os.listdir('accounts_data'):
        if filename.endswith('.json'):
            filepath = os.path.join('accounts_data', filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if data['personal']['account_name'] == username:
                    data['personal']['balance'] = balance
                    with open(filepath, 'w', encoding='utf-8') as file:
                        json.dump(data, file, indent=4)
                    break
    else:
        not_found.append(f"{username} {balance}")

with open('not_found.txt', 'w', encoding='utf-8') as file:
    for account in not_found:
        file.write(f"{account}\n")
