from datetime import datetime, timedelta
import discord
from discord.ext import commands, tasks
import json
import asyncio
from data_handler import DataHandler
import random
from mimic_handler import MimicHandler

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

with open(config['data_path'], 'r') as f:
    data_path = f.read().strip()

# Create the bot instance
intents = discord.Intents(guilds=True, messages=True, message_content=True)
client = commands.Bot(command_prefix='!', intents=intents)

# Initialize DataHandler with path from configuration
data_handler = DataHandler(data_path)

# Initialize MimicHandler with DataHandler instance
mimic_handler = MimicHandler(data_handler)

mimic_data = {}


@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')

@client.command()
async def scrape(ctx, confirm: str = None):
    key = f'{ctx.author.name}_{ctx.guild.name}'
    existing_filename = data_handler.check_for_existing_csv(key)
    if existing_filename and confirm != "yes":
        await ctx.send(
            "You already have saved messages. Would you like to overwrite them? Respond with `!scrape yes` to overwrite.")
    elif existing_filename and confirm == "yes":
        await data_handler.perform_scraping(ctx, key, client)
    else:
        await data_handler.perform_scraping(ctx, key, client)


@client.command()
async def mimic_random(ctx):
    await mimic_handler.mimic_random(ctx)


@client.command()
async def r(ctx, *args):
    await mimic_handler.r(ctx, *args)


@client.command()
async def clear(ctx):
    await mimic_handler.clear(ctx)


@client.command()
async def mimic_ai(ctx):
    await mimic_handler.mimic_ai(ctx)


# Run the bot
with open('token.txt', 'r') as file:
    token = file.read().strip()
client.run(token)