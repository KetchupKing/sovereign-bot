import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import json
import aiofiles
import re
import glob

ACCOUNTS_DATA_DIR = os.path.join(os.path.dirname(__file__), 'accounts_data')
COMPANY_DATA_DIR = os.path.join(os.path.dirname(__file__), 'company_data')
os.makedirs(ACCOUNTS_DATA_DIR, exist_ok=True)
os.makedirs(COMPANY_DATA_DIR, exist_ok=True)
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
load_dotenv()
TOKEN = os.getenv('TOKEN')


async def log_interaction(ctx):
    async with aiofiles.open('command_log.txt', mode='a') as f:
        await f.write(f"Command '{ctx.command.name}' used by {ctx.author.name}\n")


def save_company_account_changes(account_name, accounts):
    file_name = os.path.join(COMPANY_DATA_DIR, '*.json')
    files = glob.glob(file_name)
    for file in files:
        with open(file, 'r') as f:
            existing_accounts = json.load(f)
            for account_id, account_info in existing_accounts.items():
                if (account_info['command_name'] == account_name or account_info['account_name'] == account_name):
                    existing_accounts[account_id] = accounts
                    with open(file, 'w') as f_write:
                        json.dump(existing_accounts, f_write, indent=4)
                    return True
    return False


def load_accounts(user_id=None, account_type=None, account_name=None):
    if account_type == "company":
        file_name = os.path.join(COMPANY_DATA_DIR, '*.json')
        files = glob.glob(file_name)
        for file in files:
            with open(file, 'r') as f:
                accounts = json.load(f)
                for account_id, account_info in accounts.items():
                    if account_name and (account_info['command_name'] == account_name or account_info['account_name'] == account_name):
                        return account_info
    else:
        personal_file_name = os.path.join(ACCOUNTS_DATA_DIR, f"{user_id}.json")
        try:
            with open(personal_file_name, 'r') as f:
                personal_accounts = json.load(f)
                return personal_accounts
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            print(f"Error: {personal_file_name} is empty or not properly formatted.")
    return None



def save_accounts(user_id, accounts, account_type=None, account_name=None):
    if account_type == "company":
        file_name = os.path.join(COMPANY_DATA_DIR, f"{account_name}.json")
    else:
        file_name = os.path.join(ACCOUNTS_DATA_DIR, f"{user_id}.json")
    with open(file_name, 'w') as f:
        json.dump(accounts, f, indent=4)


def check_or_create_account(user_id):
    accounts = load_accounts(user_id)
    if not accounts:
        accounts = {
            "personal": {
                "balance": 1000,
                "currency": "gold",
                "own accounts": [],
                "treasurer of": []
            }
        }
        save_accounts(user_id, accounts)
        return "A new personal account named 'personal' has been created with an initial balance of 1000 gold."
    else:
        return f"Your account balance is {accounts['personal']['balance']} {accounts['personal']['currency']}."

def create_new_account(ctx, user_id, account_name, command_name, account_type):
    

    accounts = load_accounts(user_id, account_type) if load_accounts(user_id, account_type) else {}

    account_id = command_name
    treasurers = [user_id] if account_type == "company" else []
    accounts[account_id] = {
        "account_name": account_name,
        "command_name": command_name,
        "account_type": account_type,
        "balance": 1000,
        "currency": "gold",
        "treasurers": treasurers,
        "owner": user_id
    }
    personal_accounts = load_accounts(user_id)
    if personal_accounts == None:
        return f"You need a personal account before you can create a company account"
    personal_accounts["personal"]["own accounts"].append(account_name)
    save_accounts(user_id, personal_accounts)
    save_accounts(user_id, accounts, account_type, account_name)
    return f"Account '{account_name}' with command name '{command_name}', type '{account_type}', balance 1000 gold, has been created."


@bot.event
async def on_ready():
    print(f'Successfully logged in {bot.user}')


@bot.slash_command(name="account", description="Check or create a personal account.")
async def account(ctx):
    user_id = str(ctx.author.id)
    response = check_or_create_account(user_id)
    await ctx.respond(response)
    await log_interaction(ctx)


@bot.slash_command(name="create_account", description="Create a new account with specified details.")
async def create_account(ctx, account_name: str, command_name: str, account_type: str):
    account_type_choices = ["company", "government"]

    if account_type not in account_type_choices:
        await ctx.respond("Invalid account type. Please choose from 'company' or 'government'.")
        return
    
    user_id = str(ctx.author.id)
    response = create_new_account(ctx, user_id, account_name, command_name, account_type)
    await ctx.respond(response)
    await log_interaction(ctx)


@bot.slash_command(name="list_accounts", description="List the personal account, owned accounts, and accounts the user is a treasurer for.")
async def list_accounts(ctx):
    user_id = str(ctx.author.id)
    personal_accounts = load_accounts(user_id)
    company_accounts = {}
    
    file_name = os.path.join(COMPANY_DATA_DIR, '*.json')
    files = glob.glob(file_name)
    for file in files:
        with open(file, 'r') as f:
            accounts = json.load(f)
            for account_id, account_info in accounts.items():
                if user_id in account_info["treasurers"] or user_id == account_info["owner"]:
                    company_accounts[account_info["account_name"]] = account_info
    
    owned_accounts = []
    treasurer_accounts = []
    
    for account_name, account_info in company_accounts.items():
        if user_id == account_info["owner"]:
            owned_accounts.append(account_name)
        elif user_id in account_info["treasurers"]:
            treasurer_accounts.append(account_name)
    
    response = ""
    if "personal" in personal_accounts:
        response += f"Personal Account: {personal_accounts['personal']['balance']} {personal_accounts['personal']['currency']}\n"
    if owned_accounts:
        response += f"Owned Accounts: {', '.join(owned_accounts)}\n"
    if treasurer_accounts:
        response += f"Treasurer For: {', '.join(treasurer_accounts)}\n"
    
    if response:
        await ctx.respond(f"Your accounts:\n{response}")
    else:
        await ctx.respond("You do not own or manage any accounts.")
    await log_interaction(ctx)


@bot.slash_command(name="treasurer_add", description="Add a treasurer to an account.")
async def add_treasurer(ctx, account_name: str, treasurer_name: str):
    user_id = str(ctx.author.id)
    account_to_modify = load_accounts(account_type="company", account_name=account_name)
    
    if account_to_modify is None:
        await ctx.respond(f"Account with name '{account_name}' does not exist.")
        return
    
    if user_id != account_to_modify.get("owner", ""):
        await ctx.respond("You are not the owner of this account.")
        return
    
    match = re.search(r'<@!?(\d+)>', treasurer_name)
    if match:
        treasurer_id = match.group(1)
        if treasurer_id not in account_to_modify["treasurers"]:
            account_to_modify["treasurers"].append(treasurer_id)
            if save_company_account_changes(account_name, account_to_modify):
                treasurer_accounts = load_accounts(treasurer_id)
                treasurer_accounts["personal"]["treasurer of"].append(account_name)
                save_accounts(treasurer_id, treasurer_accounts)
                await ctx.respond(f"Treasurer '{treasurer_name}' has been added to '{account_name}'.")
            else:
                await ctx.respond("Failed to save changes.")
        else:
            await ctx.respond(f"Treasurer '{treasurer_name}' is already added to '{account_name}'.")
    else:
        await ctx.respond("Invalid treasurer mention.")
    await log_interaction(ctx)


@bot.slash_command(name="treasurer_remove", description="Remove a treasurer from an account.")
async def remove_treasurer(ctx, account_name: str, treasurer_name: str):
    user_id = str(ctx.author.id)
    account_to_modify = load_accounts(account_type="company", account_name=account_name)
    
    if account_to_modify is None:
        await ctx.respond(f"Account with name '{account_name}' does not exist.")
        return
    
    if user_id != account_to_modify.get("owner", ""):
        await ctx.respond("You are not the owner of this account.")
        return
    
    match = re.search(r'<@!?(\d+)>', treasurer_name)
    if match:
        treasurer_id = match.group(1)
        if treasurer_id in account_to_modify["treasurers"]:
            account_to_modify["treasurers"].remove(treasurer_id)
            if save_company_account_changes(account_name, account_to_modify):
                treasurer_accounts = load_accounts(treasurer_id)
                treasurer_accounts["personal"]["treasurer of"].remove(account_name)
                save_accounts(treasurer_id, treasurer_accounts)
                await ctx.respond(f"Treasurer '{treasurer_name}' has been removed from '{account_name}'.")
            else:
                await ctx.respond("Failed to save changes.")
        else:
            await ctx.respond(f"Treasurer '{treasurer_name}' is not added to '{account_name}'.")
    else:
        await ctx.respond("Invalid treasurer mention.")
    await log_interaction(ctx)




@bot.slash_command(name="treasurer_list", description="List all treasurers for an account.")
async def list_treasurers(ctx, account_name: str):
    user_id = str(ctx.author.id)
    account_to_list = load_accounts(account_type="company", account_name=account_name)
    
    if account_to_list is None:
        await ctx.respond(f"Account with name '{account_name}' does not exist.")
        return
    
    if user_id != account_to_list.get("owner", ""):
        await ctx.respond("You are not the owner of this account.")
        return
    
    treasurers = account_to_list["treasurers"]
    if treasurers:
        treasurer_names = []
        for treasurer_id in treasurers:
            user = await bot.fetch_user(int(treasurer_id))
            treasurer_names.append(user.display_name)
        await ctx.respond(f"Treasurers for '{account_name}': {', '.join(treasurer_names)}")
    else:
        await ctx.respond(f"No treasurers found for '{account_name}'.")
    await log_interaction(ctx)



@bot.slash_command(name="pay", description="Transfer an amount from one account to another.")
async def pay(
    ctx,
    amount: int = discord.Option(description="The amount to transfer"),
    account_to_pay: discord.User = discord.Option(discord.User, description="The user to pay", required=False),
    account_name: str = discord.Option(description="The name of the account to pay", required=False),
    from_account: str = discord.Option(description="The account from which to transfer", required=False),
    tax_account: str = discord.Option(description="The account to add tax to", required=False),
    tax_percentage: int = discord.Option(description="Percentage of tax to subtract", required=False),
    memo: str = discord.Option(description="A memo for the transaction", required=False)
):
    
    amountNumber = int(amount)

    sender_id = str(ctx.author.id)
    recipient_id = str(account_to_pay.id) if account_to_pay else None


    if from_account:
        #print(from_account)
        sender_accounts = load_accounts(account_type="company", account_name=from_account)
        print(sender_accounts)
        if sender_accounts is None:
            await ctx.respond("The specified 'from account' does not exist.")
            return
    else:
        sender_accounts = load_accounts(sender_id)
        #print(sender_accounts)
        if sender_accounts is None:
            await ctx.respond("You do not have a personal account.")
            return
        
    transactionType = None    

    if "personal" in sender_accounts:
        print("paying from personal account")
        if sender_accounts["personal"]["balance"] < amountNumber:
            await ctx.respond("Insufficient funds.")
            return
        else:
            sender_accounts["personal"]["balance"] -= amountNumber
            save_accounts(sender_id, sender_accounts)   

            transactionType = "personal"
    elif sender_accounts["account_type"] == "company":
        print("paying from company account")
        if sender_accounts["balance"] < amountNumber:
            await ctx.respond("Insufficient funds in the company account.")
            return
        else:
            sender_accounts["balance"] -= amountNumber
            save_company_account_changes(from_account,sender_accounts)
            transactionType = "company"

    if account_name:
        #print(account_name)
        recipient_accounts = load_accounts(account_type="company", account_name=account_name)
        #print(recipient_accounts)
        if recipient_accounts is None:
            await ctx.respond("The specified 'account name' does not exist.")
            return
    else:
        recipient_accounts = load_accounts(recipient_id)
        #print(recipient_accounts)
        if recipient_accounts is None:
            await ctx.respond("The recipient does not have a personal account.")
            return

    if tax_percentage and tax_account:
        taxPercentage = int(tax_percentage)
        taxAccount = load_accounts(account_type="company", account_name=tax_account)
        
        taxAmount = round(amountNumber*(taxPercentage/100))
        newAmount = round(amountNumber-taxAmount)
        print(f"sending to recipient: {newAmount}, sending to tax target: {taxAmount}")

        taxAccount["balance"] += taxAmount
        print(tax_account)
        save_company_account_changes(tax_account,taxAccount)


    if "personal" in recipient_accounts:
        if tax_percentage and tax_account:
            recipient_accounts["personal"]["balance"] += newAmount
            save_accounts(recipient_id, recipient_accounts)
        else:
            recipient_accounts["personal"]["balance"] += amountNumber
            save_accounts(recipient_id, recipient_accounts)

    elif recipient_accounts["account_type"] == "company":
        if tax_percentage and tax_account:
            recipient_accounts["balance"] += newAmount
            save_company_account_changes(account_name,recipient_accounts)
        else:
            recipient_accounts["balance"] += amountNumber
            save_company_account_changes(account_name,recipient_accounts)
    
    response_message = f"Successfully paid {amountNumber} {sender_accounts["currency"] if transactionType == "company" else sender_accounts["personal"]["currency"]} to '{account_to_pay.name if account_to_pay else account_name}' from {sender_accounts["account_name"] if transactionType == "company" else "personal account"}."
    if memo:
        response_message += f" Memo: {memo}."
    if tax_percentage and tax_account:
        response_message += f" With {tax_percentage}% tax to '{taxAccount["account_name"]}'"
    await ctx.respond(response_message)
    await log_interaction(ctx)
    
    
#bot.run(TOKEN)
