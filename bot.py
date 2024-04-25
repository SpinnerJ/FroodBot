from datetime import datetime, timedelta
import discord
from discord.ext import commands
import os
import csv
import pandas as pd
from openai import OpenAI


class DataHandler:
    def __init__(self, base_path):
        self.base_path = base_path

    def save_messages_to_csv(self, key, messages):
        if not messages:
            return None
        safe_key = self._sanitize_key(key)
        filename = os.path.join(self.base_path, f'{safe_key}.csv')
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Message'])
            writer.writerows([[msg] for msg in messages])
        return filename

    def load_messages_from_csv(self, key):
        safe_key = self._sanitize_key(key)
        filename = os.path.join(self.base_path, f'{safe_key}.csv')
        if not os.path.exists(filename):
            return []
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            return [row[0] for row in reader if row]

    def _sanitize_key(self, key):
        return "".join(c for c in key if c.isalnum() or c in (' ', '_')).replace(' ', '_')


client = commands.Bot(command_prefix='!', intents=discord.Intents(guilds=True, messages=True, message_content=True))

with open('key.txt', 'r') as file:
    OPEN_AI_KEY = file.read().strip()

openai_client = OpenAI(api_key=OPEN_AI_KEY)

@client.command()
async def scrape(ctx):
    key = f'{ctx.author.name}_{ctx.guild.name}'
    await ctx.send('Scraping your messages. Please wait...')
    messages = await scrape_user_messages(ctx.author, ctx.guild)
    if not messages:
        await ctx.send("No messages found or an error occurred.")
    else:
        filename = data_handler.save_messages_to_csv(key, messages)
        if filename:
            await ctx.send("Messages saved.")
@client.command()
async def analyzeme(ctx, arg=''):
    try:
        if arg.lower() == 'yes':
            key = f'{ctx.author.name}_{ctx.guild.name}'
            await ctx.send("Scraping your messages. Please wait...")
            messages = await scrape_user_messages(ctx.author, ctx.guild)
            if not messages:
                await ctx.send("No messages found or an error occurred.")
            else:
                filename = data_handler.save_messages_to_csv(key, messages)
                if filename:
                    await ctx.send("Messages saved. Starting analysis...")
                    analysis_results = await analyze_messages(filename)
                    await ctx.send(f"Analysis complete:\n{analysis_results}")
                else:
                    await ctx.send("Failed to save messages.")
        elif arg == '':
            await ctx.send(
                "This command will scrape your past messages in non-NSFW channels for analysis. Do you consent to this? "
                "If yes, reply with `!analyzeme yes`. This operation is subject to data privacy regulations and the data will only be used for analysis."
            )
        else:
            await ctx.send("Command aborted.")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
        # Log the error or further handle it as necessary


async def analyze_messages(filename):
    messages = data_handler.load_messages_from_csv(os.path.basename(filename).split('.')[0])
    text = " ".join(messages)
    response = await openai_client.completions.create(
        model="gpt-3.5-turbo",
        prompt=f"Analyze the following text to find the top 3 topics discussed and the attitudes towards each: {text}",
        max_tokens=150
    )
    return response['choices'][0]['text'].strip()


async def scrape_user_messages(user, guild):
    end_time = datetime.now() + timedelta(minutes=5)
    limit = 1000
    messages = []
    i = 0
    for channel in guild.text_channels:
        if not channel.is_nsfw():
            try:
                async for message in channel.history(limit=None, oldest_first=False):
                    if message.author == user:
                        messages.append(message.content)
                        i += 1
                        print(i)
                        if len(messages) >= limit or datetime.now() > end_time:
                            return messages
            except discord.errors.Forbidden:
                continue  # Skip channels where the bot does not have permissions
    return messages


with open('token.txt', 'r') as file:
    token = file.read().strip()
with open('path.txt', 'r') as file:
    path = file.read().strip()

data_handler = DataHandler(path)
client.run(token)
