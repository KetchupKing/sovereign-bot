from discord.ext import commands
from discord.ui import Button, View
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
		print(current_time)
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


def removeAccount(accountName):
	file_name = os.path.join(COMPANY_DATA_DIR, f'{accountName}.json')
	os.remove(file_name)
	print(file_name)


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
				print(authorised)
	
			if user_id in authorised:
				file_name = os.path.join(COMPANY_DATA_DIR, '*.json')
				files = glob.glob(file_name)
	
				for file in files:
					with open(file, 'r') as f:
						accounts = json.load(f)

						for account_id, account_info in accounts.items():
		
							if account_name and (account_info['command_name'] == account_name or account_info['account_name'] == account_name):
								print(account_info)
								return account_info

		else:
			personal_file_name = os.path.join(ACCOUNTS_DATA_DIR, f"{user_id}.json")
			print(personal_file_name)
			try:
				with open(personal_file_name, 'r') as f:
					personal_accounts = json.load(f)
					print(personal_accounts)
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
			print(file_name)

		elif account_type == "government":
			file_name = os.path.join(COMPANY_DATA_DIR, f"{account_name}.json")
			print(file_name)

		else:
			file_name = os.path.join(ACCOUNTS_DATA_DIR, f"{user_id}.json")
			print(file_name)
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


def check_or_create_account(user_id, userName):
	try:
		accounts = load_accounts(user_id)
		print(accounts)

		if not accounts:
			from_account = 'Cieurnish Treasury'
			sender_account = load_accounts(account_type="Company", account_name=from_account)
			sender_account["balance"] -= 300
			save_company_account_changes(from_account, sender_account)

			accounts = {
				"personal": {
					"account_name": userName,
					"balance": 300,
					"currency": "Sovereign",
					"own accounts": [],
					"treasurer of": []
				}
			}
			save_accounts(user_id, accounts)
			return "A new personal account has been created."

		else:
			return f"Your account balance is Sv {accounts['personal']['balance']:,}."
	except:
		return("check_or_create_account error, please contact Ketchup & manfred with this")


def create_new_account(ctx, user_id, account_name, command_name, account_type):
	try:
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
		print(accounts)
		account_id = command_name
		print(account_id)
		treasurers = [user_id]
		print(treasurers)
		
		if account_type == "Company":
			accounts[account_id] = {
				"account_name": account_name,
				"command_name": command_name,
				"account_type": account_type,
				"balance": 0,
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
					"balance": 0,
					"currency": "Sovereign",
					"treasurers": treasurers,
					"owner": user_id
				}
			else:
				return "You need to be an authorised user"

		personal_accounts = load_accounts(user_id)
		print(personal_accounts)

		if personal_accounts == None:
			return f"You need a personal account before you can create a Company account"
		personal_accounts["personal"]["own accounts"].append(account_name)
		save_accounts(user_id, personal_accounts)
		save_accounts(user_id, accounts, account_type, account_name)
		return f"Account '{account_name}' with command name '{command_name}', type '{account_type}', has been created."
	except:
		return("create_new_account error, please contact Ketchup & manfred with this")


def sort_accounts():
	try:
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
	except:
		return("sort_accounts error, please contact Ketchup & manfred with this")


def getItemsOnPage(lst, page_num, items_per_page=10):
	try:
		start_index = (page_num - 1) * items_per_page
		end_index = min(start_index + items_per_page, len(lst))
		return lst[start_index:end_index]
	except:
		return("getItemsOnPage error, please contact Ketchup & manfred with this")


def tax(amount, tax_account, tax_percentage):
	global new_amount
	tax_percentage = round(tax_percentage, 3)
	tax_percentage = int(tax_percentage)

	if tax_percentage > 100 or tax_percentage < 0:
		return "Only put tax between 100 and 0"

	Tax_Account = load_accounts(account_type="Company", account_name=tax_account)
	tax_amount = round(amount*(tax_percentage/100))
	Tax_Account["balance"] += tax_amount
	new_amount = amount - tax_amount
	save_company_account_changes(tax_account,Tax_Account)
	return new_amount, Tax_Account, tax_amount


def load_user_settings():
	global user_settings
	try:
		with open('user_settings.json', 'r') as f:
			user_settings = json.load(f)
	except FileNotFoundError:
		user_settings = {}
	except json.JSONDecodeError:
		user_settings = {}
	except Exception as e:
		print(f"Error loading user settings: {e}")
		user_settings = {}


def save_user_settings():
	with open('user_settings.json', 'w') as f:
		json.dump(user_settings, f, indent=4)


def should_send_notification(user_id):
	return user_settings.get(user_id, True)


@bot.event
async def on_ready():
	print(f'Successfully logged in {bot.user}')


@bot.slash_command(name="ping", description="Replies with Pong!")
async def ping(
	ctx,
	ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
	try:
		log_event(ctx.author.id, ctx.author.name, "ping", {"ephemeral": ephemeral})
		await ctx.respond("Pong!", ephemeral=ephemeral)
	except:
		await ctx.respond("ping command error, please contact Ketchup & manfred with this")


@bot.slash_command(name="pong", description="Replies with Ping!")
async def pong(
	ctx,
	ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
	try:
		log_event(ctx.author.id, ctx.author.name, "pong", {"ephemeral": ephemeral})
		await ctx.respond("Ping!", ephemeral=ephemeral)
	except:
		await ctx.respond("pong command error, please contact Ketchup & manfred with this")


@bot.slash_command(name="account", description="Check or create a personal account.")
async def account(
	ctx,
	ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
	try:
		log_event(ctx.author.id, ctx.author.name, "account", {"ephemeral": ephemeral})
		user_id = str(ctx.author.id)
		print(user_id)
		userName = str(ctx.author.name)
		print(userName)
		response = check_or_create_account(user_id, userName)
		print(response)
		await ctx.respond(response, ephemeral=ephemeral)
	except:
		await ctx.respond("account command error, please contact Ketchup & manfred with this")


@bot.slash_command(name="create_account", description="Create a Company/government account with specified details.")
async def create_account(
	ctx, 
	account_name: str, 
	command_name: str, 
	account_type: str = discord.Option(str, choices=['Company', 'government']),
	ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
	try:
		log_event(ctx.author.id, ctx.author.name, "create_account", {"account_name": account_name, "command_name": command_name, "account_type": account_type, "ephemeral": ephemeral})
		account_type_choices = ["Company", "government"]

		if account_type not in account_type_choices:
			await ctx.respond("Invalid account type. Please choose from 'Company' or 'government'.", ephemeral=ephemeral)
			return

		user_id = str(ctx.author.id)
		print(user_id)
		response = create_new_account(ctx, user_id, account_name, command_name, account_type)
		print(response)
		await ctx.respond(response, ephemeral=ephemeral)
	except:
		await ctx.respond("create_account command error, please contact Ketchup & manfred with this")


@bot.slash_command(name="list_accounts", description="List the personal account, owned accounts, and accounts the user is a treasurer for.")
async def list_accounts(
	ctx,
	ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
	try:
		log_event(ctx.author.id, ctx.author.name, "list_accounts", {"ephemeral": ephemeral})
		user_id = str(ctx.author.id)
		print(user_id)
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
				response += f"Personal Account: ㏜{personal_accounts['personal']['balance']:,}\n"
				embed.add_field(name=f"{personal_accounts['personal']['account_name']}'s account (Personal)", value=f"Command Name: N/A\nBalance: ㏜{personal_accounts['personal']['balance']:,}")

			if owned_accounts:

				for i, (account_name, account_info) in enumerate(owned_accounts, start=1):
					response += f"{account_name}: {account_info['balance']} {account_info['currency']}\n"
					embed.add_field(name=f"{account_name} ({account_info['account_type']})", value=f"Command Name: {account_info['command_name']}\nBalance: ㏜{account_info['balance']:,}", inline=False)

			if treasurer_accounts:

				for i, (account_name, account_info) in enumerate(treasurer_accounts, start=1):
					embed.add_field(name=f"{account_name} ({account_info['account_type']}) (Treasurer)", value=f"Command Name: {account_info['command_name']}\nBalance: ㏜{account_info['balance']:,}", inline=False)

		else:
			await ctx.respond("You do not own or manage any accounts.", ephemeral=ephemeral)
			return

		if embed:
			await ctx.respond(embed=embed, ephemeral=ephemeral)
	except:
		await ctx.respond("list_accounts command error, please contact Ketchup & manfred with this")


@bot.slash_command(name="treasurer_add", description="Add a treasurer to an account.")
async def add_treasurer(
	ctx, 
	account_name: str = discord.Option(description="Name of account adding a treasurer to"),
	treasurer_name: discord.User = discord.Option(discord.User, description="Name of treasurer adding"),
	ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
	try:
		log_event(ctx.author.id, ctx.author.name, "treasurer_add", {"account_name": account_name, "treasurer_name": treasurer_name.name, "ephemeral": ephemeral})
		user_id = str(ctx.author.id)
		print(user_id)
		account_to_modify = load_accounts(account_type="Company", account_name=account_name)

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

	except:
		await ctx.respond("treasurer_add command error, please contact Ketchup & manfred with this")


@bot.slash_command(name="treasurer_remove", description="Remove a treasurer from an account.")
async def remove_treasurer(
	ctx, 
	account_name: str = discord.Option(description="Name of account removing a treasurer from"),
	treasurer_name: discord.User = discord.Option(discord.User, description="Name of treasurer removing"),
	ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
	try:
		log_event(ctx.author.id, ctx.author.name, "treasurer_remove", {"account_name": account_name, "treasurer_name": treasurer_name.name, "ephemeral": ephemeral})
		user_id = str(ctx.author.id)
		print(user_id)
		account_to_modify = load_accounts(account_type="Company", account_name=account_name)
		
		if account_to_modify is None:
			await ctx.respond(f"Account with name '{account_name}' does not exist.", ephemeral=ephemeral)
			return

		if user_id != account_to_modify.get("owner", ""):
			await ctx.respond("You are not the owner of this account.", ephemeral=ephemeral)
			return
		
		treasurer_id = str(treasurer_name.id)
		print(treasurer_id)

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

	except:
		await ctx.respond("treasurer_remove command error, please contact Ketchup & manfred with this")


@bot.slash_command(name="treasurer_list", description="List all treasurers for an account.")
async def list_treasurers(
	ctx, 
	account_name: str = discord.Option(description="Account to list treasurers of"),
	ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
	try:
		log_event(ctx.author.id, ctx.author.name, "treasurer_list", {"account_name": account_name, "ephemeral": ephemeral})
		user_id = str(ctx.author.id)
		print(user_id)
		account_to_list = load_accounts(account_type="Company", account_name=account_name)
		
		if account_to_list is None:
			await ctx.respond(f"Account with name '{account_name}' does not exist.", ephemeral=ephemeral)
			return

		if user_id != account_to_list["owner"] and not user_id in account_to_list["treasurers"]:
			await ctx.respond("You are not the owner of this account.", ephemeral=ephemeral)
			return
		
		treasurers = account_to_list["treasurers"]
		print(treasurers)
		
		if treasurers:
			treasurer_names = []

			for treasurer_id in treasurers:
				user = await bot.fetch_user(int(treasurer_id))
				treasurer_names.append(user.display_name)
			await ctx.respond(f"Treasurers for '{account_name}': {', '.join(treasurer_names)}", ephemeral=ephemeral)

		else:
			await ctx.respond(f"No treasurers found for '{account_name}'.", ephemeral=ephemeral)

	except:
		await ctx.respond("treasurer_list command error, please contact Ketchup & manfred with this")


@bot.slash_command(name="toggle_notifications", description="Toggle notifications on or off.")
async def toggle_notifications(ctx):
	user_id = str(ctx.author.id)
	if user_id not in user_settings:
		user_settings[user_id] = True
	user_settings[user_id] = not user_settings[user_id]
	save_user_settings()
	log_event(user_id, ctx.author.name, "toggle_notifications", {"new_setting": user_settings[user_id]})
	await ctx.respond(f"Notifications toggled to {'on' if user_settings[user_id] else 'off'} for you.")


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
	try:
		log_event(ctx.author.id, ctx.author.name, "pay", {"amount": amount, "account_to_pay": account_to_pay.name if account_to_pay else None, "account_name": account_name, "from_account": from_account, "tax_account": tax_account, "tax_percentage": tax_percentage, "memo": memo, "ephemeral": ephemeral})
		sender_id = str(ctx.author.id)
		recipient_id = str(account_to_pay.id) if account_to_pay else account_name

		if account_to_pay and not from_account and not account_name:
			sender_account = load_accounts(sender_id)
			recipient_account = load_accounts(recipient_id)

			if sender_id == recipient_id:
				await ctx.respond("Your not allowed to pay yourself", ephemeral=ephemeral)
				return

			elif tax_percentage and tax_account:

				if sender_account["personal"]["balance"] >= new_amount:
					new_amount, Tax_Account, tax_amount = tax(amount, tax_account, tax_percentage)
					sender_account["personal"]["balance"] -= amount
					recipient_account["personal"]["balance"] += new_amount
					save_accounts(sender_id, accounts=sender_account)
					save_accounts(recipient_id, accounts=recipient_account)
					await ctx.respond(f"Successfully paid ㏜{new_amount:,} to {account_to_pay.name}. \nWith {tax_percentage}% tax to '{Tax_Account['account_name']}' (㏜{tax_amount:,})", ephemeral=ephemeral)
					if should_send_notification(recipient_id):
						await account_to_pay.send(f"You have received a payment of ㏜{amount:,} from {ctx.author.name}\nWith {tax_percentage}% tax to '{Tax_Account['account_name']}' (㏜{tax_amount}). \nMemo: {memo}.")

					if memo:
						await ctx.respond(f" Memo: {memo}.", ephemeral=ephemeral)
					return

				else:
					await ctx.respond("Insufficient balance.", ephemeral=ephemeral)
					return

			else:

				if sender_account["personal"]["balance"] >= amount:
					sender_account["personal"]["balance"] -= amount
					recipient_account["personal"]["balance"] += amount
					save_accounts(sender_id, accounts=sender_account)
					save_accounts(recipient_id, accounts=recipient_account)
					await ctx.respond(f"Successfully paid ㏜{amount:,} to {account_to_pay.name}.", ephemeral=ephemeral)
					if should_send_notification(recipient_id):
						await account_to_pay.send(f"You have received a payment of ㏜{amount:,} from {ctx.author.name}. \nMemo: {memo}.")

					if memo:
						await ctx.respond(f" Memo: {memo}.", ephemeral=ephemeral)
					return

				else:
					await ctx.respond("Insufficient balance.", ephemeral=ephemeral)
					return

		elif account_to_pay and from_account and not account_name:
			sender_account = load_accounts(account_type="Company", account_name=from_account)
			recipient_account = load_accounts(recipient_id)

			if sender_id not in sender_account["treasurers"]:
				await ctx.respond("Your not allowed to pay from this account", ephemeral=ephemeral)
				return

			if sender_account == recipient_account:
				await ctx.respond("Your not allowed to pay yourself", ephemeral=ephemeral)
				return

			if sender_account is None:
				await ctx.respond("The specified 'from account' does not exist.", ephemeral=ephemeral)
				return

			elif tax_percentage and tax_account:

				if sender_account["balance"] >= amount:
					new_amount, Tax_Account, tax_amount = tax(amount, tax_account, tax_percentage)
					sender_account["balance"] -= amount
					recipient_account["personal"]["balance"] += new_amount
					save_company_account_changes(from_account, sender_account)
					save_accounts(recipient_id, accounts=recipient_account)
					await ctx.respond(f"Successfully paid ㏜{new_amount:,} to {account_to_pay.name} from account {from_account}. \nWith {tax_percentage}% tax to '{Tax_Account['account_name']}' (㏜{tax_amount:,})", ephemeral=ephemeral)
					if should_send_notification(recipient_id):
						await account_to_pay.send(f"You have received a payment of ㏜{amount:,} from {from_account}\nWith {tax_percentage}% tax to '{Tax_Account['account_name']}' (㏜{tax_amount}). \nMemo: {memo}.")


					if memo:
						await ctx.respond(f" Memo: {memo}.", ephemeral=ephemeral)
					return

				else:
					await ctx.respond("Insufficient balance.", ephemeral=ephemeral)
					return

			else:

				if sender_account["balance"] >= amount:
					sender_account["balance"] -= amount
					recipient_account["personal"]["balance"] += amount
					save_company_account_changes(from_account, sender_account)
					save_accounts(recipient_id, accounts=recipient_account)
					await ctx.respond(f"Successfully paid ㏜{amount:,} to {account_to_pay.name} from account {from_account}.", ephemeral=ephemeral)
					if should_send_notification(recipient_id):
						await account_to_pay.send(f"You have received a payment of ㏜{amount:,} from {from_account}. \nMemo: {memo}.")

					if memo:
						await ctx.respond(f" Memo: {memo}.", ephemeral=ephemeral)
					return

				else:
					await ctx.respond("Insufficient balance.", ephemeral=ephemeral)
					return

		elif account_name and not account_to_pay and not from_account:
			sender_account = load_accounts(sender_id)
			recipient_account = load_accounts(account_type="Company", account_name=account_name)

			if sender_account == recipient_account:
				await ctx.respond("Your not allowed to pay yourself", ephemeral=ephemeral)
				return

			if recipient_account is None:
				await ctx.respond("The specified account to pay does not exist.", ephemeral=ephemeral)
				return

			if sender_account is None:
				await ctx.respond("The specified 'from account' does not exist.", ephemeral=ephemeral)
				return

			elif tax_percentage and tax_account:

				if sender_account["personal"]["balance"] >= amount:
					new_amount, Tax_Account, tax_amount = tax(amount, tax_account, tax_percentage)
					sender_account["personal"]["balance"] -= amount
					recipient_account["balance"] += new_amount
					save_accounts(sender_id, accounts=sender_account)
					save_company_account_changes(account_name, recipient_account)
					await ctx.respond(f"Successfully paid ㏜{new_amount:,} to {account_name}. \nWith {tax_percentage}% tax to '{Tax_Account['account_name']}' (㏜{tax_amount:,})", ephemeral=ephemeral)

					if memo:
						await ctx.respond(f" Memo: {memo}.", ephemeral=ephemeral)
					return

				else:
					await ctx.respond("Insufficient balance.", ephemeral=ephemeral)
					return

			else:

				if sender_account["personal"]["balance"] >= amount:
					sender_account["personal"]["balance"] -= amount
					recipient_account["balance"] += amount
					save_accounts(sender_id, accounts=sender_account)
					save_company_account_changes(account_name, recipient_account)
					await ctx.respond(f"Successfully paid ㏜{amount:,} to {account_name}.", ephemeral=ephemeral)

					if memo:
						await ctx.respond(f" Memo: {memo}.", ephemeral=ephemeral)
					return

				else:
					await ctx.respond("Insufficient balance.", ephemeral=ephemeral)
					return

		elif account_name and from_account and not account_to_pay:
			sender_account = load_accounts(account_type="Company", account_name=from_account)
			recipient_account = load_accounts(account_type="Company", account_name=account_name)

			if sender_id not in sender_account["treasurers"]:
				await ctx.respond("Your not allowed to pay from this account", ephemeral=ephemeral)
				return

			if sender_account == recipient_account:
				await ctx.respond("Your not allowed to pay yourself", ephemeral=ephemeral)
				return

			if sender_account is None:
				await ctx.respond("The specified 'from account' does not exist.", ephemeral=ephemeral)
				return

			if recipient_account is None:
				await ctx.respond("The specified account to pay does not exist.", ephemeral=ephemeral)

			elif tax_percentage and tax_account:

				if sender_account["balance"] >= amount:
					new_amount, Tax_Account, tax_amount = tax(amount, tax_account, tax_percentage)
					sender_account["balance"] -= amount
					recipient_account["balance"] += new_amount
					save_company_account_changes(from_account, sender_account)
					save_company_account_changes(account_name, recipient_account)
					await ctx.respond(f"Successfully paid ㏜{new_amount:,} to {account_name} from account {from_account}. \nWith {tax_percentage}% tax to '{Tax_Account['account_name']}' (㏜{tax_amount:,})", ephemeral=ephemeral)

					if memo:
						await ctx.respond(f" Memo: {memo}.", ephemeral=ephemeral)
					return

				else:
					await ctx.respond("Insufficient balance.", ephemeral=ephemeral)
					return

			else:

				if sender_account["balance"] >= amount:
					sender_account["balance"] -= amount
					recipient_account["balance"] += amount
					save_company_account_changes(from_account, sender_account)
					save_company_account_changes(account_name, recipient_account)
					await ctx.respond(f"Successfully paid ㏜{amount:,} to {account_name} from account {from_account}.", ephemeral=ephemeral)

					if memo:
						await ctx.respond(f" Memo: {memo}.", ephemeral=ephemeral)
					return

				else:
					await ctx.respond("Insufficient balance.", ephemeral=ephemeral)
					return

		else:
			await ctx.respond("Error")
	except:
		await ctx.respond("pay command error, please contact Ketchup & manfred with this")


@bot.slash_command(name="baltop", description="Accounts with the most Sovereigns.")
async def baltop(
	ctx, 
	page: int = discord.Option(int, description="The page number to display", required=False, default=1),
	ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
	try:
		MAX_MESSAGE_LENGTH = 2000
		log_event(ctx.author.id, ctx.author.name, "baltop", {"page": page, "ephemeral": ephemeral})
		sorted_accounts = sort_accounts()
		nAccounts = len(sorted_accounts)
		maxPages = math.ceil(nAccounts/10)

		if page > maxPages:
			page = maxPages
		if page < 1:
			page = 1

		trimmed_accounts = getItemsOnPage(sorted_accounts, page)
		response = f"Top balances in the system: (Page: {page}/{maxPages})\n"

		for i, (account_id, account_info) in enumerate(trimmed_accounts, start=1):
			account_name = account_info.get('account_name')
			formatted_balance = f"{account_info['balance']:,}"
			account_line = f"#{i+((page-1)*10)} - {account_name} - Sv{formatted_balance} \n"

			if len(response) + len(account_line) > MAX_MESSAGE_LENGTH:
				await ctx.respond(response, ephemeral=ephemeral)
				response = account_line

			else:
				response += account_line

		if response:
			await ctx.respond(response, ephemeral=ephemeral)

	except:
		await ctx.respond("baltop command error, please contact Ketchup & manfred with this")


@bot.slash_command(name="authorisation", description="Authorise users to do government accounts.")
async def authorise(
	ctx,
	user_to_add: discord.User = discord.Option(discord.User, description="The user to authorise", required=False),
	user_to_remove: discord.User = discord.Option(discord.User, description="The user to un-authorise", required=False),
	ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
	try:
		log_event(ctx.author.id, ctx.author.name, "authorisation", {"user_to_add": user_to_add.name if user_to_add else None, "user_to_remove": user_to_remove.name if user_to_remove else None, "ephemeral": ephemeral})
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

	except:
		await ctx.respond("authorisation command error, please contact Ketchup & manfred with this")


@bot.slash_command(name="eco", description="Manage account balances.")
async def eco(
	ctx,
	user: discord.User = discord.Option(discord.User, description="Person to interact with", required=False),
	account: str = discord.Option(str, description="Account to interact with", required=False),
	command: str = discord.Option(str, description="Command", required=False),
	value: int = discord.Option(int, description="The value", required=False),
	ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
):
	try:
		log_event(ctx.author.id, ctx.author.name, "eco", {"user": user.name if user else None, "account": account, "command": command, "value": value, "ephemeral": ephemeral})
		user_id = str(ctx.author.id)
		recipient_id = str(user.id) if user else None

		if account:
			recipient_accounts = load_accounts(account_type="Company", account_name=account)

			if recipient_accounts is None:
				await ctx.respond("The specified 'account name' does not exist.", ephemeral=True)
				return
		else:
			recipient_accounts = load_accounts(recipient_id)

			if recipient_accounts is None:
				await ctx.respond("The recipient does not have a personal account.", ephemeral=ephemeral)
				return

		if user_id in admin:

			if command == "set":
				print(recipient_accounts)

				if "personal" in recipient_accounts:
					recipient_accounts["personal"]["balance"] = value
					save_accounts(recipient_id, recipient_accounts)

				elif recipient_accounts["account_type"] == "Company":
					recipient_accounts["balance"] = value
					save_company_account_changes(account,recipient_accounts)
				
			elif command == "add":

				if "personal" in recipient_accounts:
					recipient_accounts["personal"]["balance"] += value
					save_accounts(recipient_id, recipient_accounts)

				elif recipient_accounts["account_type"] == "Company":
					recipient_accounts["balance"] += value
					save_company_account_changes(account,recipient_accounts)

			elif command == "sub":

				if "personal" in recipient_accounts:
					recipient_accounts["personal"]["balance"] -= value
					save_accounts(recipient_id, recipient_accounts)

				elif recipient_accounts["account_type"] == "Company":
					recipient_accounts["balance"] -= value
					save_company_account_changes(account,recipient_accounts)
					
			await ctx.respond(recipient_accounts)

		else:
			await ctx.respond("You are not admin")

	except:
		await ctx.respond("eco command error, please contact Ketchup & manfred with this")


@bot.slash_command(name="transfer_account", description="Transfer or something")
async def transfer_account(
	ctx,
	account_name: str = discord.Option(str, description="Account to transfer", required=True),
	transfer_to = discord.Option(discord.User, description="Account to transfer to", required=True)
):
	try:
		log_event(ctx.author.id, ctx.author.name, "transfer_account", {"account_name": account_name, "transfer_to": transfer_to.name})
		account = load_accounts(account_type="Company", account_name=account_name)

		if str(ctx.author.id) == account["owner"]:
			confirmButton = Button(label="Confirm account transfer", style=discord.ButtonStyle.danger, emoji="✅")

			async def button_callback(interaction):

				if interaction.user.id == ctx.author.id:
					account["owner"] = str(transfer_to.id)
					account["treasurers"].remove(str(ctx.author.id))
					account["treasurers"].append(str(transfer_to.id))
					save_company_account_changes(account_name, account)
					await interaction.response.send_message(f"Transferring {account_name} to {str(transfer_to.name)}")
				
			confirmButton.callback = button_callback
			view = View()
			view.add_item(confirmButton)

			await ctx.respond(f"Do you want to transfer the account {account_name}", view=view)

		else:
			await ctx.respond("You are not the owner of this account")

	except:
		await ctx.respond("transfer_account command error, please contact Ketchup & manfred with this")


@bot.slash_command(name="remove_account", description="Remove account")
async def remove_account(
	ctx,
	account_name: str = discord.Option(str, description="Account to remove", required=True)
):
	try:
		log_event(ctx.author.id, ctx.author.name, "remove_account", {"account_name": account_name})
		account = load_accounts(account_type="Company", account_name=account_name)

		if str(ctx.author.id) == account["owner"]:

			if account["balance"] == 0:
				confirmButton = Button(label="Confirm account removal", style=discord.ButtonStyle.danger, emoji="✅")

				async def button_callback(interaction):

					if interaction.user.id == ctx.author.id:
						removeAccount(account["account_name"])
						await interaction.response.send_message(f"ok removing then....")

				confirmButton.callback = button_callback
				view = View()
				view.add_item(confirmButton)

				await ctx.respond(f"Do you want to delete the account {account_name}", view=view)

			else:
				await ctx.respond(f"Empty account before removing")
	except:
		await ctx.respond("remove_account command error, please contact Ketchup & manfred with this")


#@bot.slash_command(name="account_all", description="Create a personal account for everyone in the server.")
#async def account_all(
#	ctx,
#	ephemeral: bool = discord.Option(bool, description="Make the response ephemeral", required=False, default=False)
#):
#	try:
#		log_event(ctx.author.id, ctx.author.name, "account_all", {"ephemeral": ephemeral})
#		user_id = str(ctx.author.id)
#
#		if user_id in admin:
#			members = await ctx.guild.fetch_members().flatten()
#
#			for member in members:
#				user_id = str(member.id)
#				userName = str(member.name)
#				accounts = load_accounts(user_id)
#
#				if not accounts:
#					accounts = {
#						"personal": {
#							"account_name": userName,
#							"balance": 0,
#							"currency": "Sovereign",
#							"own accounts": [],
#							"treasurer of": []
#						}
#					}
#					save_accounts(user_id, accounts)
#					print(f"A new personal account has been created for {userName}.")
#
#				else:
#					print(f"{userName} already has an account.")
#			await ctx.respond("All personal accounts have been created.", ephemeral=ephemeral)
#
#		else:
#			await ctx.respond("You do not have permission to use this command.", ephemeral=ephemeral)
#
#	except:
#		await ctx.respond("account_all command error, please contact Ketchup & manfred with this")

load_user_settings()
bot.run(TOKEN)
