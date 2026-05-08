import discord
from discord.ext import commands
import requests
import os

# Your Discord bot token from Railway env vars
TOKEN = os.environ.get('DISCORD_TOKEN')
# Your live API URL
API_URL = "https://web-production-2528.up.railway.app/check"

# Bot setup with message content intent
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} is online and checking rugs!')
    print(f'Connected to {len(bot.guilds)} servers')

@bot.command(name="rug")
async def rug_check(ctx, address: str, chain: str = "solana"):
    """Check if a token is a potential rug. Usage:!rug <address> [chain]"""

    await ctx.send(f"🔍 Scanning `{address[:6]}...{address[-4:]}` on {chain}...")

    try:
        response = requests.get(f"{API_URL}?address={address}&chain={chain}", timeout=10)
        data = response.json()

        if "error" in data:
            embed = discord.Embed(
                title="❌ No Data Found",
                description=data.get("reason", "Token has no liquidity or address is wrong"),
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        # Rug score logic based on liquidity
        liquidity = data.get("liquidity_usd", 0)
        if liquidity < 50000:
            risk = "🔴 HIGH RISK"
            color = 0xff0000
        elif liquidity < 500000:
            risk = "🟡 MEDIUM RISK"
            color = 0xffcc00
        else:
            risk = "🟢 LOW RISK"
            color = 0x00ff00

        embed = discord.Embed(
            title=f"RugCheck: ${data['token_symbol']}",
            description=f"**{data.get('token_name', 'Unknown')}**",
            color=color
        )
        embed.add_field(name="Price", value=f"${data.get('price_usd', 0):.8f}", inline=True)
        embed.add_field(name="Risk Level", value=risk, inline=True)
        embed.add_field(name="Liquidity", value=f"${liquidity:,.2f}", inline=True)
        embed.add_field(name="FDV", value=f"${data.get('fdv', 0):,.0f}", inline=True)
        embed.add_field(name="24h Volume", value=f"${data.get('volume_24h', 0):,.2f}", inline=True)
        embed.add_field(name="DEX", value=data.get('dex', 'Unknown').title(), inline=True)
        embed.set_footer(text="Data from DexScreener | Not financial advice")

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"⚠️ API error: {str(e)}")

bot.run(TOKEN)
