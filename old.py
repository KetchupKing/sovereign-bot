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
#					#print(f"A new personal account has been created for {userName}.")
#
#				else:
#					#print(f"{userName} already has an account.")
#			await ctx.respond("All personal accounts have been created.", ephemeral=ephemeral)
#
#		else:
#			await ctx.respond("You do not have permission to use this command.", ephemeral=ephemeral)
#
#	except:
#		await ctx.respond("account_all command error, please contact Ketchup & manfred with this")
