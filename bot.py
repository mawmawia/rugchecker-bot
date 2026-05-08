import discord
from discord.ext import commands
import requests
import os
from datetime import datetime

# --- CONFIG ---
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
API_URL = "https://web-production-53f05.up.railway.app" # Your API URL

# --- PAYWALL SETUP ---
PRO_SERVERS = [] # Add paid server IDs here: [123456789012345678, 987654321098765432]
FREE_CHECKS_USED = {} # Tracks daily usage per server
FREE_LIMIT = 3 # Free checks per day per server

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def check_paywall(ctx):
    """Returns True if allowed, False if blocked + sends paywall message"""
    if ctx.guild.id in PRO_SERVERS:
        return True

    today = datetime.now().strftime('%Y-%m-%d')
    key = f"{ctx.guild.id}-{today}"
    uses = FREE_CHECKS_USED.get(key, 0)

    if uses >= FREE_LIMIT:
        embed = discord.Embed(
            title="🚫 Daily Free Limit Reached",
            description=f"This server used all {FREE_LIMIT} free checks today.\n\n**Upgrade to RugChecker Pro - $29/mo**\n✅ Unlimited ETH + SOL checks\n✅ Priority API speed\n✅ New LP unlock alerts\n\n**DM `Mawia steve` to upgrade**",
            color=0xff4444
        )
        return False

    FREE_CHECKS_USED[key] = uses + 1
    return True

@bot.event
async def on_ready():
    print(f'{bot.user} is online and checking rugs!')
    print(f'Connected to {len(bot.guilds)} servers')

@bot.command()
async def check(ctx, address):
    # PAYWALL CHECK
    if not check_paywall(ctx):
        return await ctx.send(embed=discord.Embed(
            title="🚫 Daily Free Limit Reached",
            description=f"This server used all {FREE_LIMIT} free checks today.\n\n**Upgrade to RugChecker Pro - $29/mo**\n✅ Unlimited ETH + SOL checks\n✅ Priority API speed\n\n**DM `Mawia steve` to upgrade**",
            color=0xff4444
        ))

    # YOUR EXISTING ETH CHECK CODE
    try:
        response = requests.get(f"{API_URL}/check?address={address}", timeout=10)
        data = response.json()

        embed = discord.Embed(
            title=f"RugCheck: {data.get('token_name', 'Unknown')}",
            description=f"**Risk Level: {data.get('risk_level', 'Unknown')}**",
            color=0x00ff00 if data.get('risk_level') == 'LOW RISK' else 0xff0000
        )
        embed.add_field(name="Score", value=f"{data.get('score', 0)}/100", inline=True)
        embed.add_field(name="Liquidity", value=f"${data.get('liquidity', 0):,.2f}", inline=True)
        embed.add_field(name="Warnings", value="\n".join(data.get('warnings', ['None'])), inline=False)

        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error checking token: {str(e)}")

@bot.command()
async def rug(ctx, address):
    # PAYWALL CHECK
    if not check_paywall(ctx):
        return await ctx.send(embed=discord.Embed(
            title="🚫 Daily Free Limit Reached",
            description=f"This server used all {FREE_LIMIT} free checks today.\n\n**Upgrade to RugChecker Pro - $29/mo**\n✅ Unlimited ETH + SOL checks\n✅ Priority API speed\n\n**DM `Mawia steve` to upgrade**",
            color=0xff4444
        ))

    # YOUR EXISTING SOL CHECK CODE
    try:
        response = requests.get(f"{API_URL}/rug?address={address}", timeout=10)
        data = response.json()

        embed = discord.Embed(
            title=f"RugCheck: {data.get('token_name', 'Unknown')}",
            description=f"**Risk Level: {data.get('risk_level', 'Unknown')}**",
            color=0x00ff00 if data.get('risk_level') == 'LOW RISK' else 0xff0000
        )
        embed.add_field(name="Score", value=f"{data.get('score', 0)}/100", inline=True)
        embed.add_field(name="Liquidity", value=f"${data.get('liquidity', 0):,.2f}", inline=True)
        embed.add_field(name="Data Source", value=data.get('source', 'DexScreener'), inline=True)
        embed.add_field(name="Warnings", value="\n".join(data.get('warnings', ['None'])), inline=False)

        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error checking token: {str(e)}")

@bot.command()
async def pro(ctx):
    """Show upgrade info"""
    embed = discord.Embed(
        title="RugChecker Pro - $29/month",
        description="Stop your members getting rugged",
        color=0x5865F2
    )
    embed.add_field(name="✅ Unlimited Checks", value="No daily limits on!rug or!check", inline=False)
    embed.add_field(name="⚡ Priority Speed", value="Faster API responses", inline=False)
    embed.add_field(name="🔔 LP Alerts [Coming Soon]", value="Get pinged when liquidity unlocks", inline=False)
    embed.add_field(name="How to Upgrade", value="DM `Mawia steve` with your Server ID", inline=False)

    if ctx.guild.id in PRO_SERVERS:
        embed.add_field(name="Status", value="✅ This server is PRO", inline=False)
    else:
        uses = FREE_CHECKS_USED.get(f"{ctx.guild.id}-{datetime.now().strftime('%Y-%m-%d')}", 0)
        embed.add_field(name="Status", value=f"FREE - {uses}/{FREE_LIMIT} checks used today", inline=False)

    await ctx.send(embed=embed)

bot.run(DISCORD_TOKEN)
