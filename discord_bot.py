import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import json
import aiofiles
import os

# Define the path to the folder where JSON files will be stored
ACCOUNTS_DATA_DIR = os.path.join(os.path.dirname(__file__), 'accounts_data')

# Ensure the directory exists
os.makedirs(ACCOUNTS_DATA_DIR, exist_ok=True)
##################################################################

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

##################################################################

load_dotenv()
TOKEN = os.getenv('TOKEN')

##################################################################

async def log_interaction(ctx):
    async with aiofiles.open('command_log.txt', mode='a') as f:
        await f.write(f"Command '{ctx.command.name}' used by {ctx.author.name}\n")

##################################################################

def load_accounts(user_id):
    file_name = os.path.join(ACCOUNTS_DATA_DIR, f"{user_id}.json")
    try:
        with open(file_name, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Error: {file_name} is empty or not properly formatted.")
        return {}

##################################################################

def save_accounts(user_id, accounts):
    file_name = os.path.join(ACCOUNTS_DATA_DIR, f"{user_id}.json")
    with open(file_name, 'w') as f:
        json.dump(accounts, f, indent=4)

##################################################################

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

##################################################################

def create_new_account(ctx, user_id, account_name, command_name, account_type):
    accounts = load_accounts(user_id)
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
    save_accounts(user_id, accounts)
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
    accounts = load_accounts(user_id)
    response_list = []
    
    if "personal" in accounts:
        response_list.append(f"Personal Account: {accounts['personal']['balance']} {accounts['personal']['currency']}")

    for account_id, account_info in accounts.items():
        if account_id != "personal" and (ctx.author.name in account_info["treasurers"] or account_info.get("owner", "") == ctx.author.name):
            response_list.append(f"{account_info['account_name']}: {account_info['balance']} {account_info['currency']}")

    if response_list:
        response = "\n".join(response_list)
        await ctx.respond(f"Your accounts:\n{response}")
    else:
        await ctx.respond("You do not own or manage any accounts.")
    await log_interaction(ctx)


@bot.slash_command(name="treasurer_add", description="Add a treasurer to an account.")
async def add_treasurer(ctx, account_name: str, treasurer_name: str):
    user_id = str(ctx.author.id)
    print(user_id)
    accounts = load_accounts(user_id)
    if account_name in accounts:
        if user_id == accounts[account_name].get("owner", ""):
            if treasurer_name not in accounts[account_name]["treasurers"]:
                accounts[account_name]["treasurers"].append(treasurer_name)
                save_accounts(user_id, accounts)
                await ctx.respond(f"Treasurer '{treasurer_name}' has been added to '{account_name}'.")
            else:
                await ctx.respond(f"Treasurer '{treasurer_name}' is already added to '{account_name}'.")
        else:
            await ctx.respond("You are not the owner of this account.")
    else:
        await ctx.respond(f"Account '{account_name}' does not exist.")
    await log_interaction(ctx)


@bot.slash_command(name="treasurer_remove", description="Remove a treasurer from an account.")
async def remove_treasurer(ctx, account_name: str, treasurer_name: str):
    user_id = str(ctx.author.id)
    accounts = load_accounts(user_id)
    if account_name in accounts:
        if ctx.author.name == accounts[account_name].get("owner", ""):
            if treasurer_name in accounts[account_name]["treasurers"]:
                accounts[account_name]["treasurers"].remove(treasurer_name)
                save_accounts(user_id, accounts)
                await ctx.respond(f"Treasurer '{treasurer_name}' has been removed from '{account_name}'.")
            else:
                await ctx.respond(f"Treasurer '{treasurer_name}' is not added to '{account_name}'.")
        else:
            await ctx.respond("You are not the owner of this account.")
    else:
        await ctx.respond(f"Account '{account_name}' does not exist.")
    await log_interaction(ctx)


@bot.slash_command(name="treasurer_list", description="List all treasurers for an account.")
async def list_treasurers(ctx, account_name: str):
    user_id = str(ctx.author.id)
    accounts = load_accounts(user_id)
    if account_name in accounts:
        treasurers = accounts[account_name]["treasurers"]
        if treasurers:
            await ctx.respond(f"Treasurers for '{account_name}': {', '.join(treasurers)}")
        else:
            await ctx.respond(f"No treasurers found for '{account_name}'.")
    else:
        await ctx.respond(f"Account '{account_name}' does not exist.")
    await log_interaction(ctx)


bot.run(TOKEN)
