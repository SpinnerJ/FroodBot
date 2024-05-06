import csv
import os
import json
import datetime
import discord
from datetime import datetime as dt, timedelta


class DataHandler:
    def __init__(self, base_path):
        self.base_path = base_path
        os.makedirs(os.path.dirname(self.base_path), exist_ok=True)
        self.scraping_in_progress = False
        self.scraping_queue = []

    def save_messages_to_csv(self, key, message_pairs):
        if not message_pairs:
            return None
        safe_key = self._sanitize_key(key)
        filename = os.path.join(self.base_path, f'{safe_key}.csv')
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Query', 'Response'])
            writer.writerows(message_pairs)
        return filename

    async def perform_scraping(self, ctx, key, client):
        if self.scraping_in_progress:
            self.scraping_queue.append((ctx, key))
            await ctx.send('Scraping is currently in progress. Your request has been added to the queue.')
            return

        self.scraping_in_progress = True
        await ctx.send('Scraping your messages. Please wait...')
        end_time = dt.now() + timedelta(minutes=5)
        limit = 1000
        messages = []
        capture_next = False
        header = True
        previous_message = None
        for channel in ctx.guild.text_channels:
            if not channel.is_nsfw():
                try:
                    async for message in channel.history(limit=None, oldest_first=False):
                        if message.content.startswith('!') or not message.content.strip():
                            continue
                        if message.author == ctx.author:
                            if previous_message:
                                messages.append(["User message", previous_message.content, "Response", message.content])
                            previous_message = message
                        elif previous_message and previous_message.author != ctx.author:
                            messages.append(["User message", previous_message.content, "Response", message.content])
                            previous_message = None

                        if len(messages) >= limit or dt.now() > end_time:
                            break
                except discord.errors.Forbidden:
                    await ctx.send(f"Bot does not have 'Read Message History' permission in channel: {channel.name}")
                    continue
        if messages:
            filename = self.save_messages_to_csv(key, messages)
            await ctx.send(f"Messages saved!")
        else:
            await ctx.send("No messages found or an error occurred during scraping.")
        self.scraping_in_progress = False
        if self.scraping_queue:
            next_ctx, next_key, next_client = self.scraping_queue.pop(0)
            await self.perform_scraping(next_ctx, next_key, next_client)
        return messages

    def load_messages_from_csv(self, key):
        safe_key = self._sanitize_key(key)
        filename = os.path.join(self.base_path, f'{safe_key}.csv')
        if not os.path.exists(filename):
            return []
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header
            return [row for row in reader]

    def check_for_existing_csv(self, key):
        safe_key = self._sanitize_key(key)
        filename = os.path.join(self.base_path, f'{safe_key}.csv')
        return os.path.exists(filename)

    def _sanitize_key(self, key):
        return "".join(c for c in key if c.isalnum() or c in (' ', '_')).replace(' ', '_')

    import csv

    def preprocess_data(input_file, output_file):
        with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
            reader = csv.reader(infile)
            next(reader)  # Skip header
            conversation = []
            for row in reader:
                if row[0].lower().startswith('query'):
                    if conversation:
                        outfile.write("\n".join(conversation) + "\n\n")
                    conversation = []
                if row[1].strip():
                    conversation.append(row[1].strip())
            if conversation:
                outfile.write("\n".join(conversation) + "\n")

    def preprocess_data(self, key):
        safe_key = self._sanitize_key(key)
        input_file = os.path.join(self.base_path, f'{safe_key}.csv')
        output_file = os.path.join(self.base_path, f'{safe_key}_preprocessed.txt')

        with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
            reader = csv.reader(infile)
            next(reader)  # Skip header
            conversation = []
            for row in reader:
                if row[0].lower().startswith('query'):
                    if conversation:
                        outfile.write("\n".join(conversation) + "\n\n")
                    conversation = []
                if row[1].strip():
                    conversation.append(row[1].strip())
            if conversation:
                outfile.write("\n".join(conversation) + "\n")