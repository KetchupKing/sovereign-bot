import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import json
import aiofiles
import re
import glob
import logging
import math

admin = ['1018934971810979840', '365931996129787914']
authorised_users = 'authorised.json'

logging.getLogger('discord').setLevel(logging.WARNING)
logging.basicConfig(filename='discord_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ACCOUNTS_DATA_DIR = os.path.join(os.path.dirname(__file__), 'accounts_data')
COMPANY_DATA_DIR = os.path.join(os.path.dirname(__file__), 'company_data')
os.makedirs(ACCOUNTS_DATA_DIR, exist_ok=True)
os.makedirs(COMPANY_DATA_DIR, exist_ok=True)
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
load_dotenv()
TOKEN = os.getenv('TOKEN')


def log_event(user_id, command_name, options):
    log_entry = {
        "user_id": user_id,
        "command_name": command_name,
        "options": options
    }
    with open('discord_bot.log', 'a') as log_file:
        log_file.write(json.dumps(log_entry) + '\n')
        logs_to_txt()


def logs_to_txt(filename='discord_log.txt'):
    with open('discord_bot.log', 'r') as log_file, open(filename, 'w') as output_file:
        for line in log_file:
            try:
                log_entry = json.loads(line)
                template_string = "User ID: {user_id}, Command: {command_name}, Options: {options}"
                options_str = ', '.join(f"{key}: {value}" for key, value in log_entry['options'].items())
                formatted_entry = template_string.format(user_id=log_entry['user_id'], command_name=log_entry['command_name'], options=options_str)
                output_file.write(formatted_entry + '\n')
            except json.JSONDecodeError:
                print(f"Error parsing line: {line}")


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


def load_accounts(user_id=None, account_type=None, account_name=None, command_name=None):
    if account_type == "company":
        file_name = os.path.join(COMPANY_DATA_DIR, '*.json')
        files = glob.glob(file_name)
        for file in files:
            with open(file, 'r') as f:
                accounts = json.load(f)
                for account_id, account_info in accounts.items():
                    if account_name and (account_info['command_name'] == account_name or account_info['account_name'] == account_name):
                        return account_info

    elif account_type == "government":
        with open(authorised_users, 'r') as f:
            authorised = json.load(f)
        if user_id in authorised:
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
    elif account_type == "government":
        file_name = os.path.join(COMPANY_DATA_DIR, f"{account_name}.json")
    else:
        file_name = os.path.join(ACCOUNTS_DATA_DIR, f"{user_id}.json")
    with open(file_name, 'w') as f:
        json.dump(accounts, f, indent=4)


def check_or_create_account(user_id, userName):
    accounts = load_accounts(user_id)
    if not accounts:
        accounts = {
            "personal": {
                "account_name": userName,
                "balance": 1000,
                "currency": "Sovereign",
                "own accounts": [],
                "treasurer of": []
            }
        }
        save_accounts(user_id, accounts)
        return "A new personal account named 'personal' has been created with an initial balance of 1000 Sovereign."
    else:
        return f"Your account balance is {accounts['personal']['balance']} {accounts['personal']['currency']}."


def create_new_account(ctx, user_id, account_name, command_name, account_type):
    all_accounts = {}
    file_name = os.path.join(COMPANY_DATA_DIR, '*.json')
    files = glob.glob(file_name)
    for file in files:
        with open(file, 'r') as f:
            accounts = json.load(f)
            all_accounts.update(accounts)

    for account_id, account_info in all_accounts.items():
        if account_info['account_name'] == account_name or account_info['command_name'] == command_name:
            return f"Error: The account name '{account_name}' or command name '{command_name}' is already in use."
    
    accounts = load_accounts(user_id, account_type) if load_accounts(user_id, account_type) else {}
    account_id = command_name
    treasurers = [user_id]
    
    if account_type == "company":
        accounts[account_id] = {
            "account_name": account_name,
            "command_name": command_name,
            "account_type": account_type,
            "balance": 1000,
            "currency": "Sovereign",
            "treasurers": treasurers,
            "owner": user_id
        }
    
    if account_type == "government":
        with open(authorised_users, 'r') as f:
            authorised = json.load(f)
        if user_id in authorised:
            accounts[account_id] = {
                "account_name": account_name,
                "command_name": command_name,
                "account_type": account_type,
                "balance": 1000,
                "currency": "Sovereign",
                "treasurers": treasurers,
                "owner": user_id
            }
        else:
            return "You need to be an authorised user"

    personal_accounts = load_accounts(user_id)
    if personal_accounts == None:
        return f"You need a personal account before you can create a company account"
    personal_accounts["personal"]["own accounts"].append(account_name)
    save_accounts(user_id, personal_accounts)
    save_accounts(user_id, accounts, account_type, account_name)
    return f"Account '{account_name}' with command name '{command_name}', type '{account_type}', balance 1000 Sovereign, has been created."


def sort_accounts():
    all_accounts = []

    for file_name in glob.glob(os.path.join(COMPANY_DATA_DIR, '*.json')):
        with open(file_name, 'r') as f:
            accounts = json.load(f)
            for account_id, account_info in accounts.items():
                if 'account_name' in account_info and 'balance' in account_info:
                    all_accounts.append((account_id, account_info))
    
    for file_name in glob.glob(os.path.join(ACCOUNTS_DATA_DIR, '*.json')):
        with open(file_name, 'r') as f:
            accounts = json.load(f)
            for account_id, account_info in accounts.items():
                if 'account_name' in account_info and 'balance' in account_info:
                    all_accounts.append((account_id, account_info))

    sorted_accounts = sorted(all_accounts, key=lambda x: x[1]['balance'], reverse=True)

    return sorted_accounts


def getItemsOnPage(lst, page_num, items_per_page=10):
    start_index = (page_num - 1) * items_per_page
    end_index = min(start_index + items_per_page, len(lst))
    return lst[start_index:end_index]


@bot.event
async def on_ready():
    print(f'Successfully logged in {bot.user}')


@bot.slash_command(name="ping", description="Replies with Pong!")
async def ping(
    ctx,
    ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
    log_event(ctx.author.id, "ping", {"ephemeral": ephemeral})
    await ctx.respond("Pong!", ephemeral=ephemeral)


@bot.slash_command(name="pong", description="Replies with Ping!")
async def pong(
    ctx,
    ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
    log_event(ctx.author.id, "pong", {"ephemeral": ephemeral})
    await ctx.respond("Ping!", ephemeral=ephemeral)


@bot.slash_command(name="account", description="Check or create a personal account.")
async def account(
    ctx,
    ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
    log_event(ctx.author.id, "account", {"ephemeral": ephemeral})
    user_id = str(ctx.author.id)
    userName = str(ctx.author.name)
    response = check_or_create_account(user_id, userName)
    await ctx.respond(response, ephemeral=ephemeral)    

@bot.slash_command(name="create_account", description="Create a company/government account with specified details.")
async def create_account(
    ctx, 
    account_name: str, 
    command_name: str, 
    account_type: str = discord.Option(str, choices=['company', 'government']),
    ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
    log_event(ctx.author.id, "create_account", {"account_name": account_name, "command_name": command_name, "account_type": account_type, "ephemeral": ephemeral})
    account_type_choices = ["company", "government"]

    if account_type not in account_type_choices:
        await ctx.respond("Invalid account type. Please choose from 'company' or 'government'.", ephemeral=ephemeral)
        return
    
    user_id = str(ctx.author.id)
    response = create_new_account(ctx, user_id, account_name, command_name, account_type)
    await ctx.respond(response, ephemeral=ephemeral)


@bot.slash_command(name="list_accounts", description="List the personal account, owned accounts, and accounts the user is a treasurer for.")
async def list_accounts(
    ctx,
    ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
    log_event(ctx.author.id, "list_accounts", {"ephemeral": ephemeral})
    user_id = str(ctx.author.id)
    personal_accounts = load_accounts(user_id)
    company_accounts = {}
    print("test 1")
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
            owned_accounts.append([account_name, account_info])
        elif user_id in account_info["treasurers"]:
            treasurer_accounts.append([account_name, account_info])

    embed = discord.Embed(
        title="Your accounts",
        description="All accounts you own and are a treasurer of",
        color=discord.Colour.green(),
    )
    response = ""
    
    if personal_accounts:
        if "personal" in personal_accounts:
            response += f"Personal Account: {personal_accounts['personal']['balance']} {personal_accounts['personal']['balance']}\n"
            embed.add_field(name=f"{personal_accounts['personal']['account_name']}'s account (Personal)", value=f"Command Name: N/A\nBalance: ㏜{personal_accounts['personal']['balance']}")

        if owned_accounts:
            for i, (account_name, account_info) in enumerate(owned_accounts, start=1):
                response += f"{account_name}: {account_info['balance']} {account_info['currency']}\n"
                embed.add_field(name=f"{account_name.capitalize()} ({account_info['account_type']})", value=f"Command Name: {account_info['command_name']}\nBalance: ㏜{account_info['balance']}",inline=False)

        if treasurer_accounts:
            for i, (account_name, account_info) in enumerate(treasurer_accounts, start=1):
                embed.add_field(name=f"{account_name.capitalize()} ({account_info['account_type']}) (Treasurer)", value=f"Command Name: {account_info['command_name']}\nBalance: ㏜{account_info['balance']}",inline=False)
    else:
        await ctx.respond("You do not own or manage any accounts.", ephemeral=ephemeral)
        return
    if embed:
        await ctx.respond(embed=embed, ephemeral=ephemeral)



@bot.slash_command(name="treasurer_add", description="Add a treasurer to an account.")
async def add_treasurer(
    ctx, 
    account_name: str = discord.Option(description="Name of account adding a treasurer to"),
    treasurer_name: discord.User = discord.Option(discord.User, description="Name of treasurer adding"),
    ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
    log_event(ctx.author.id, "treasurer_add", {"account_name": account_name, "treasurer_name": treasurer_name.name, "ephemeral": ephemeral})
    user_id = str(ctx.author.id)
    account_to_modify = load_accounts(account_type="company", account_name=account_name)
    
    if account_to_modify is None:
        await ctx.respond(f"Account with name '{account_name}' does not exist.", ephemeral=ephemeral)
        return
    
    if user_id != account_to_modify.get("owner", ""):
        await ctx.respond("You are not the owner of this account.", ephemeral=ephemeral)
        return
    
    treasurer_id = str(treasurer_name.id)
    
    if treasurer_id not in account_to_modify["treasurers"]:
        account_to_modify["treasurers"].append(treasurer_id)
        if save_company_account_changes(account_name, account_to_modify):
            treasurer_accounts = load_accounts(treasurer_id)
            if treasurer_accounts is None or treasurer_accounts.get("personal") is None:
                await ctx.respond(f"Treasurer '{treasurer_name}' does not have a personal account.", ephemeral=ephemeral)
            else:
                treasurer_accounts["personal"]["treasurer of"].append(account_name)
                save_accounts(treasurer_id, treasurer_accounts)
                await ctx.respond(f"Treasurer '{treasurer_name}' has been added to '{account_name}'.", ephemeral=ephemeral)
        else:
            await ctx.respond("Failed to save changes.", ephemeral=ephemeral)
    else:
        await ctx.respond(f"Treasurer '{treasurer_name}' is already added to '{account_name}'.", ephemeral=ephemeral)


@bot.slash_command(name="treasurer_remove", description="Remove a treasurer from an account.")
async def remove_treasurer(
    ctx, 
    account_name: str = discord.Option(description="Name of account removing a treasurer from"),
    treasurer_name: discord.User = discord.Option(discord.User, description="Name of treasurer removing"),
    ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
    log_event(ctx.author.id, "treasurer_remove", {"account_name": account_name, "treasurer_name": treasurer_name.name, "ephemeral": ephemeral})
    user_id = str(ctx.author.id)
    account_to_modify = load_accounts(account_type="company", account_name=account_name)
    
    if account_to_modify is None:
        await ctx.respond(f"Account with name '{account_name}' does not exist.", ephemeral=ephemeral)
        return
    
    if user_id != account_to_modify.get("owner", ""):
        await ctx.respond("You are not the owner of this account.", ephemeral=ephemeral)
        return
    
    treasurer_id = str(treasurer_name.id)
    
    if treasurer_id in account_to_modify["treasurers"]:
        account_to_modify["treasurers"].remove(treasurer_id)
        if save_company_account_changes(account_name, account_to_modify):
            treasurer_accounts = load_accounts(treasurer_id)
            if account_name in treasurer_accounts["personal"]["treasurer of"]:
                treasurer_accounts["personal"]["treasurer of"].remove(account_name)
                save_accounts(treasurer_id, treasurer_accounts)
                await ctx.respond(f"Treasurer '{treasurer_name}' has been removed from '{account_name}'.", ephemeral=ephemeral)
            else:
                await ctx.respond(f"Treasurer '{treasurer_name}' is not managing '{account_name}'.", ephemeral=ephemeral)
        else:
            await ctx.respond("Failed to save changes.", ephemeral=ephemeral)
    else:
        await ctx.respond(f"Treasurer '{treasurer_name}' is not added to '{account_name}'.", ephemeral=ephemeral)


@bot.slash_command(name="treasurer_list", description="List all treasurers for an account.")
async def list_treasurers(
    ctx, 
    account_name: str = discord.Option(description="Account to list treasurers of"),
    ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
    log_event(ctx.author.id, "treasurer_list", {"account_name": account_name, "ephemeral": ephemeral})
    user_id = str(ctx.author.id)
    account_to_list = load_accounts(account_type="company", account_name=account_name)
    
    if account_to_list is None:
        await ctx.respond(f"Account with name '{account_name}' does not exist.", ephemeral=ephemeral)
        return
    
    print(user_id in account_to_list["treasurers"])

    if user_id != account_to_list["owner"] and not user_id in account_to_list["treasurers"]:
        await ctx.respond("You are not the owner of this account.", ephemeral=ephemeral)
        return
    
    treasurers = account_to_list["treasurers"]
    
    if treasurers:
        treasurer_names = []
        for treasurer_id in treasurers:
            user = await bot.fetch_user(int(treasurer_id))
            treasurer_names.append(user.display_name)
        await ctx.respond(f"Treasurers for '{account_name}': {', '.join(treasurer_names)}", ephemeral=ephemeral)
    else:
        await ctx.respond(f"No treasurers found for '{account_name}'.", ephemeral=ephemeral)


@bot.slash_command(name="pay", description="Transfer an amount from one account to another.")
async def pay(
    ctx,
    amount: int = discord.Option(description="The amount to transfer"),
    account_to_pay: discord.User = discord.Option(discord.User, description="The user to pay", required=False),
    account_name: str = discord.Option(description="The name of the account to pay", required=False),
    from_account: str = discord.Option(description="The account from which to transfer", required=False),
    tax_account: str = discord.Option(description="The account to add tax to", required=False),
    tax_percentage: float = discord.Option(float, description="Percentage of tax to subtract", required=False),
    memo: str = discord.Option(description="A memo for the transaction", required=False),
    ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
    
    log_event(ctx.author.id, "pay", {"amount": amount, "account_to_pay": account_to_pay.name if account_to_pay else None, "account_name": account_name, "from_account": from_account, "tax_account": tax_account, "tax_percentage": tax_percentage, "memo": memo, "ephemeral": ephemeral})

    tax_percentage = round(tax_percentage, 3)
    if tax_percentage > 100 or tax_percentage < 0:
        await ctx.respond("Only put tax between 100 and 0", ephemeral=ephemeral)
        return

    amountNumber = int(amount)

    sender_id = str(ctx.author.id)
    recipient_id = str(account_to_pay.id) if account_to_pay else None
    
    if from_account:
        sender_accounts = load_accounts(account_type="company", account_name=from_account)
        if sender_accounts is None:
            await ctx.respond("The specified 'from account' does not exist.", ephemeral=ephemeral)
            return
    else:
        sender_accounts = load_accounts(sender_id)
        if sender_accounts is None:
            await ctx.respond("You do not have a personal account.", ephemeral=ephemeral)
            return
        
    transactionType = None	

    if "personal" in sender_accounts:
        if sender_accounts["personal"]["balance"] < amountNumber:
            await ctx.respond("Insufficient funds.", ephemeral=ephemeral)
            return
        else:
            sender_accounts["personal"]["balance"] -= amountNumber
            save_accounts(sender_id, sender_accounts)
            transactionType = "personal"

    elif sender_accounts["account_type"] == "company" or sender_accounts["account_type"] == "government":
        if sender_accounts["owner"] == sender_id or sender_id in sender_accounts["treasurers"]:
            if sender_accounts["balance"] < amountNumber:
                await ctx.respond("Insufficient funds in the company account.", ephemeral=ephemeral)
                return
            else:
                sender_accounts["balance"] -= amountNumber
                save_company_account_changes(from_account,sender_accounts)
                transactionType = "company"
        else:
            await ctx.respond(f"You do not have permission for '{sender_accounts['account_name']}'", ephemeral=ephemeral)
            return

    if account_name:
        recipient_accounts = load_accounts(account_type="company", account_name=account_name)
        if recipient_accounts is None:
            await ctx.respond("The specified 'account name' does not exist.", ephemeral=True)
            return
    else:
        recipient_accounts = load_accounts(recipient_id)
        if recipient_accounts is None:
            await ctx.respond("The recipient does not have a personal account.", ephemeral=ephemeral)
            return

    if tax_percentage and tax_account:
        taxPercentage = int(tax_percentage)
        taxAccount = load_accounts(account_type="company", account_name=tax_account)
        
        taxAmount = round(amountNumber*(taxPercentage/100))
        newAmount = round(amountNumber-taxAmount)

        taxAccount["balance"] += taxAmount
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
    
    response_message = (f"Successfully paid {amountNumber} {sender_accounts['currency'] if transactionType == 'company' else sender_accounts['personal']['currency']} to '{account_to_pay.name if account_to_pay else account_name}' from {sender_accounts['account_name'] if transactionType == 'company' else 'personal account'}.")
    if memo:
        response_message += f" Memo: {memo}."
    if tax_percentage and tax_account:
        response_message += f" With {tax_percentage}% tax to '{taxAccount['account_name']}'"
    await ctx.respond(response_message, ephemeral=ephemeral)


@bot.slash_command(name="baltop", description="Accounts with the most Sovereign.")
async def baltop(
    ctx, 
    page: int = discord.Option(int,description="The amount to transfer", required=False, default=1),
    ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
    log_event(ctx.author.id, "baltop", {"page": page, "ephemeral": ephemeral})
    sorted_accounts = sort_accounts()
    trimmed_accounts = getItemsOnPage(sorted_accounts,page)
    nAccounts = len(sorted_accounts)
    maxPages = math.ceil(nAccounts/10)

    if page > maxPages:
        page = maxPages

    response = f"Accounts with the most Sovereign:  (Page: {page}/{maxPages})\n"

    for i, (account_id, account_info) in enumerate(sorted_accounts, start=1):
        account_name = account_info.get('account_name')
        response += f"{i+((page-1)*10)}. {account_name} - {account_info['balance']} Sovereign\n"
    await ctx.respond(response, ephemeral=ephemeral)


@bot.slash_command(name="authorisation", description="Authorise users to do government accounts.")
async def authorise(
    ctx,
    user_to_add: discord.User = discord.Option(discord.User, description="The user to authorise", required=False),
    user_to_remove: discord.User = discord.Option(discord.User, description="The user to un-authorise", required=False),
    ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
    #log_event(ctx.author.id, "authorise", {"adding user": user_to_add, "removing user": user_to_remove, "ephemeral": ephemeral})
    user_id = str(ctx.author.id)
    
    if user_to_add:
        authorise_id = str(user_to_add.id)
        if user_id in admin:
            if not os.path.exists(authorised_users):
                with open(authorised_users, 'w') as f:
                    json.dump([], f)
            with open(authorised_users, 'r') as f:
                authorised = json.load(f)
            
            if authorise_id not in authorised:
                authorised.append(authorise_id)
                await ctx.respond(f"{authorise_id} has been authorised", ephemeral=ephemeral)
            else:
                await ctx.respond(f"{authorise_id} is already authorised.", ephemeral=ephemeral)
            
            with open(authorised_users, 'w') as f:
                json.dump(authorised, f)

        else:
            await ctx.respond("Your not an admin.", ephemeral=ephemeral)
        
    elif user_to_remove:
        authorise_id = str(user_to_remove.id)
        if user_id in admin:
            if not os.path.exists(authorised_users):
                with open(authorised_users, 'w') as f:
                    json.dump([], f)
            with open(authorised_users, 'r') as f:
                authorised = json.load(f)
            
            if authorise_id in authorised:
                authorised.remove(authorise_id)
                await ctx.respond(f"{authorise_id} has been un-authorised", ephemeral=ephemeral)
            else:
                await ctx.respond(f"{authorise_id} is not in the list.", ephemeral=ephemeral)

            with open(authorised_users, 'w') as f:
                json.dump(authorised, f)

        else:
            await ctx.respond("Your not an admin.", ephemeral=ephemeral)


bot.run(TOKEN)