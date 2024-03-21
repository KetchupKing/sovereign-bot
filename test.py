import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import json
import aiofiles

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

def load_accounts(user_id, account_type=None):
    personal_file_name = os.path.join(ACCOUNTS_DATA_DIR, f"{user_id}.json")
    company_file_name = os.path.join(COMPANY_DATA_DIR, f"{user_id}.json")
    
    personal_accounts = {}
    company_accounts = {}
    
    try:
        with open(personal_file_name, 'r') as f:
            personal_accounts = json.load(f)
    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        print(f"Error: {personal_file_name} is empty or not properly formatted.")
    
    try:
        with open(company_file_name, 'r') as f:
            company_accounts = json.load(f)
    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        print(f"Error: {company_file_name} is empty or not properly formatted.")
    
    if account_type == "company":
        return company_accounts
    else:
        return personal_accounts


def save_accounts(user_id, accounts, account_type=None):
    if account_type == "company":
        file_name = os.path.join(COMPANY_DATA_DIR, f"{user_id}.json")
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
                "treasurers": []
            }
        }
        save_accounts(user_id, accounts)
        return "A new personal account named 'personal' has been created with an initial balance of 1000 gold."
    else:
        return f"Your account balance is {accounts['personal']['balance']} {accounts['personal']['currency']}."

def create_new_account(ctx, user_id, account_name, command_name, account_type):
    accounts = load_accounts(user_id, account_type)
    account_id = command_name
    treasurers = [ctx.author.name] if account_type == "company" else []
    accounts[account_id] = {
        "account_name": account_name,
        "command_name": command_name,
        "account_type": account_type,
        "balance": 1000,
        "currency": "gold",
        "treasurers": treasurers,
        "owner": user_id
    }
    save_accounts(user_id, accounts, account_type)
    return f"Account '{account_name}' with command name '{command_name}', type '{account_type}', balance 1000 gold, has been created."


##################################################################




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

@bot.slash_command(name="list_accounts", description="List the name and balance of every account the user owns or is a treasurer of.")
async def list_accounts(ctx):
    user_id = str(ctx.author.id)
    personal_accounts = load_accounts(user_id)
    company_accounts = load_accounts(user_id, account_type="company")
    
    response_list = []
    
    if "personal" in personal_accounts:
        response_list.append(f"Personal Account: {personal_accounts['personal']['balance']} {personal_accounts['personal']['currency']}")
    
    for account_id, account_info in company_accounts.items():
        response_list.append(f"{account_info['account_name']}: {account_info['balance']} {account_info['currency']}")
    
    if response_list:
        response = "\n".join(response_list)
        await ctx.respond(f"Your accounts:\n{response}")
    else:
        await ctx.respond("You do not own or manage any accounts.")
    await log_interaction(ctx)



@bot.slash_command(name="treasurer_add", description="Add a treasurer to an account.")
async def add_treasurer(ctx, command_name: str, treasurer_name: str):
    user_id = str(ctx.author.id)
    accounts = load_accounts(user_id, account_type="company")
    
    if command_name in accounts:
        if user_id == accounts[command_name].get("owner", ""):
            if treasurer_name not in accounts[command_name]["treasurers"]:
                accounts[command_name]["treasurers"].append(treasurer_name)
                save_accounts(user_id, accounts, account_type="company")
                await ctx.respond(f"Treasurer '{treasurer_name}' has been added to '{accounts[command_name]['account_name']}'.")
            else:
                await ctx.respond(f"Treasurer '{treasurer_name}' is already added to '{accounts[command_name]['account_name']}'.")
        else:
            await ctx.respond("You are not the owner of this account.")
    else:
        await ctx.respond(f"Account with command name '{command_name}' does not exist.")
    await log_interaction(ctx)



@bot.slash_command(name="treasurer_remove", description="Remove a treasurer from an account.")
async def remove_treasurer(ctx, command_name: str, treasurer_name: str):
    user_id = str(ctx.author.id)
    accounts = load_accounts(user_id, account_type="company")
    
    if command_name in accounts:
        if user_id == accounts[command_name].get("owner", ""):
            if treasurer_name in accounts[command_name]["treasurers"]:
                accounts[command_name]["treasurers"].remove(treasurer_name)
                save_accounts(user_id, accounts, account_type="company")
                await ctx.respond(f"Treasurer '{treasurer_name}' has been removed from '{accounts[command_name]['account_name']}'.")
            else:
                await ctx.respond(f"Treasurer '{treasurer_name}' is not added to '{accounts[command_name]['account_name']}'.")
        else:
            await ctx.respond("You are not the owner of this account.")
    else:
        await ctx.respond(f"Account with command name '{command_name}' does not exist.")
    await log_interaction(ctx)



@bot.slash_command(name="treasurer_list", description="List all treasurers for an account.")
async def list_treasurers(ctx, command_name: str):
    user_id = str(ctx.author.id)
    accounts = load_accounts(user_id, account_type="company")
    
    if command_name in accounts:
        treasurers = accounts[command_name]["treasurers"]
        if treasurers:
            await ctx.respond(f"Treasurers for '{accounts[command_name]['account_name']}': {', '.join(treasurers)}")
        else:
            await ctx.respond(f"No treasurers found for '{accounts[command_name]['account_name']}'.")
    else:
        await ctx.respond(f"Account with command name '{command_name}' does not exist.")
    await log_interaction(ctx)



bot.run(TOKEN)
