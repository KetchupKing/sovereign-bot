from discord.ext import commands
from dotenv import load_dotenv
import aiofiles
import logging
import discord
import json
import glob
import math
import time
import os
import re

admin = ['365931996129787914', '1018934971810979840']
authorised_users = 'authorised.json'

logging.getLogger('discord').setLevel(logging.WARNING)
logging.basicConfig(filename='discord_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ACCOUNTS_DATA_DIR = os.path.join(os.path.dirname(__file__), 'accounts_data')
COMPANY_DATA_DIR = os.path.join(os.path.dirname(__file__), 'company_data')
os.makedirs(ACCOUNTS_DATA_DIR, exist_ok=True)
os.makedirs(COMPANY_DATA_DIR, exist_ok=True)

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

load_dotenv()
TOKEN = os.getenv('TOKEN')


def log_event(user_id, user_name, command_name, options):
	try:
		current_time = int(time.time())
		log_entry = {
			"user_id": user_id,
			"user_name": user_name,
			"command_name": command_name,
			"options": options,
			"timestamp": current_time
		}
		with open('discord_bot.log', 'a') as log_file:
			log_file.write(json.dumps(log_entry) + '\n')
	except:
		return("log_event error, please contact Ketchup & manfred with this")


def load_accounts(user_id=None, account_type=None, account_name=None, command_name=None):
	try:
		if account_type == "Company":
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
	except:
		return("load_accounts error, please contact Ketchup & manfred with this")


def save_accounts(user_id, accounts, account_type=None, account_name=None):
	try:
	 
		if account_type == "Company":
			file_name = os.path.join(COMPANY_DATA_DIR, f"{account_name}.json")

		elif account_type == "government":
			file_name = os.path.join(COMPANY_DATA_DIR, f"{account_name}.json")

		else:
			file_name = os.path.join(ACCOUNTS_DATA_DIR, f"{user_id}.json")
		with open(file_name, 'w') as f:
			json.dump(accounts, f, indent=4)
	except:
		return("save_accounts error, please contact Ketchup & manfred with this")


def save_company_account_changes(account_name, accounts):
	try:
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
	except:
		return("save_company_account_changes error, please contact Ketchup & manfred with this")

@bot.event
async def on_ready():
	print(f'Successfully logged in {bot.user}')


@bot.slash_command(name="pay", description="Transfer an amount from one account to another.")
async def pay(
	ctx,
	amount: int = discord.Option(int, description="The amount to transfer"),
	account_to_pay: discord.User = discord.Option(discord.User, description="The user to pay", required=False),
	account_name: str = discord.Option(description="The name of the account to pay", required=False),
	from_account: str = discord.Option(description="The account from which to transfer", required=False),
	tax_account: str = discord.Option(description="The account to add tax to", required=False),
	tax_percentage: float = discord.Option(float, description="Percentage of tax to subtract", required=False),
	memo: str = discord.Option(description="A memo for the transaction", required=False),
	ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
	log_event(ctx.author.id, ctx.author.name, "pay", {"amount": amount, "account_to_pay": account_to_pay.name if account_to_pay else None, "account_name": account_name, "from_account": from_account, "tax_account": tax_account, "tax_percentage": tax_percentage, "memo": memo, "ephemeral": ephemeral})
	sender_id = str(ctx.author.id)
	recipient_id = str(account_to_pay.id) if account_to_pay else account_name


#account_to_pay - your personal to another personal
	if account_to_pay and not from_account and not account_name:
		if sender_id == recipient_id:
			await ctx.respond("Your not allowed to pay yourself")
			return

		elif tax_percentage and tax_account:
			tax_percentage = round(tax_percentage, 3)
			tax_percentage = int(tax_percentage)

			if tax_percentage > 100 or tax_percentage < 0:
				await ctx.respond("Only put tax between 100 and 0", ephemeral=ephemeral)
				return

			Tax_Account = load_accounts(account_type="Company", account_name=tax_account)
			tax_amount = round(amount*(tax_percentage/100))
			Tax_Account["balance"] += tax_amount
			new_amount = amount - tax_amount
			save_company_account_changes(tax_account,Tax_Account)
			sender_account = load_accounts(sender_id)
			recipient_account = load_accounts(recipient_id)

			if sender_account["personal"]["balance"] >= new_amount:
				sender_account["personal"]["balance"] -= amount
				recipient_account["personal"]["balance"] += new_amount
				save_accounts(sender_id, accounts=sender_account)
				save_accounts(recipient_id, accounts=recipient_account)
				await ctx.respond(f"Successfully paid ㏜{new_amount:,} to {account_to_pay.name}. \nWith {tax_percentage}% tax to '{Tax_Account['account_name']}' (㏜{tax_amount:,})")
				return
			else:
				await ctx.respond("Insufficient balance.", ephemeral=True)
				return

		else:
			sender_account = load_accounts(sender_id)
			recipient_account = load_accounts(recipient_id)
	
			if sender_account["personal"]["balance"] >= amount:
				sender_account["personal"]["balance"] -= amount
				recipient_account["personal"]["balance"] += amount
				save_accounts(sender_id, accounts=sender_account)
				save_accounts(recipient_id, accounts=recipient_account)
				await ctx.respond(f"Successfully paid ㏜{amount:,} to {account_to_pay.name}.")
				return
			else:
				await ctx.respond("Insufficient balance.", ephemeral=True)
				return


#account_to_pay and from_account - your company/gov to another personal
	elif account_to_pay and from_account and not account_name:
		sender_account = load_accounts(account_type="Company", account_name=from_account)
		recipient_account = load_accounts(recipient_id)

		if sender_account["treasurers"] != sender_id:
			await ctx.respond("Your not allowed to pay from this account")
			return

		if sender_account == recipient_account:
			await ctx.respond("Your not allowed to pay yourself")
			return

		elif tax_percentage and tax_account:
			if sender_account is None:
				await ctx.respond("The specified 'from account' does not exist.", ephemeral=ephemeral)
				return

			tax_percentage = round(tax_percentage, 3)
			tax_percentage = int(tax_percentage)

			if tax_percentage > 100 or tax_percentage < 0:
				await ctx.respond("Only put tax between 100 and 0", ephemeral=ephemeral)
				return

			Tax_Account = load_accounts(account_type="Company", account_name=tax_account)
			tax_amount = round(amount*(tax_percentage/100))
			Tax_Account["balance"] += tax_amount
			new_amount = amount - tax_amount
			save_company_account_changes(tax_account,Tax_Account)

			if sender_account["balance"] >= amount:
				sender_account["balance"] -= amount
				recipient_account["personal"]["balance"] += new_amount
				save_company_account_changes(from_account, sender_account)
				save_accounts(recipient_id, accounts=recipient_account)
				await ctx.respond(f"Successfully paid ㏜{new_amount:,} to {account_to_pay.name} from account {from_account}. \nWith {tax_percentage}% tax to '{Tax_Account['account_name']}' (㏜{tax_amount:,})")
				return

			else:
				await ctx.respond("Insufficient balance.", ephemeral=True)
				return

		else:
			if sender_account is None:
				await ctx.respond("The specified 'from account' does not exist.", ephemeral=ephemeral)
				return
			if sender_account["balance"] >= amount:
				sender_account["balance"] -= amount
				recipient_account["personal"]["balance"] += amount
				save_company_account_changes(from_account, sender_account)
				save_accounts(recipient_id, accounts=recipient_account)
				await ctx.respond(f"Successfully paid ㏜{amount:,} to {account_to_pay.name} from account {from_account}.")
				return
			else:
				await ctx.respond("Insufficient balance.", ephemeral=True)
				return


#account_name - your personal to company/gov
	elif account_name and not account_to_pay and not from_account:
		sender_account = load_accounts(sender_id)
		recipient_account = load_accounts(account_type="Company", account_name=account_name)

		if sender_account == recipient_account:
			await ctx.respond("Your not allowed to pay yourself")
			return

		elif tax_percentage and tax_account:
			if sender_account is None:
				await ctx.respond("The specified 'from account' does not exist.", ephemeral=ephemeral)
				return

			tax_percentage = round(tax_percentage, 3)
			tax_percentage = int(tax_percentage)

			if tax_percentage > 100 or tax_percentage < 0:
				await ctx.respond("Only put tax between 100 and 0", ephemeral=ephemeral)
				return

			Tax_Account = load_accounts(account_type="Company", account_name=tax_account)
			tax_amount = round(amount*(tax_percentage/100))
			Tax_Account["balance"] += tax_amount
			new_amount = amount - tax_amount
			save_company_account_changes(tax_account,Tax_Account)

			if sender_account["personal"]["balance"] >= amount:
				sender_account["personal"]["balance"] -= amount
				recipient_account["balance"] += new_amount
				save_accounts(sender_id, accounts=sender_account)
				save_company_account_changes(account_name, recipient_account)
				await ctx.respond(f"Successfully paid ㏜{new_amount:,} to {account_name}. \nWith {tax_percentage}% tax to '{Tax_Account['account_name']}' (㏜{tax_amount:,})")
				return

			else:
				await ctx.respond("Insufficient balance.", ephemeral=True)
				return

		else:
			if sender_account is None:
				await ctx.respond("The specified 'from account' does not exist.", ephemeral=ephemeral)
				return
			if sender_account["personal"]["balance"] >= amount:
				sender_account["personal"]["balance"] -= amount
				recipient_account["balance"] += amount
				save_accounts(sender_id, accounts=sender_account)
				save_company_account_changes(account_name, recipient_account)
				await ctx.respond(f"Successfully paid ㏜{amount:,} to {account_name}.")
				return
			else:
				await ctx.respond("Insufficient balance.", ephemeral=True)
				return


#account_name and from_account - your company/gov to another company/gov
#	elif account_name and from_account:


	if memo:
		response_message += f" Memo: {memo}."

bot.run(TOKEN)
