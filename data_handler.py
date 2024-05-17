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
            writer.writerows(message_pairs)
        return filename

    def is_key_in_queue(self, user_key):
        for item in self.scraping_queue:
            ctx, key = item
            if key == user_key:
                return True
        return False


    async def perform_scraping(self, ctx, key, client):
        if self.scraping_in_progress and self.currently_scraping == key:
            await ctx.send('Your data is currently being scraped. Please wait...')
            return
        elif self.is_key_in_queue(key):
            await ctx.send('You are already in the scraping queue. Please wait...')
            return
        self.scraping_in_progress = True
        self.currently_scraping = key
        user = ctx.author
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
                        if message.content.startswith('!') or "@" in message.content or not message.content.strip():
                            continue
                        if message.author == ctx.author: #if the message is from the user
                            messages.append(["User: ", message.content])
                            if previous_message: #if there is a previous message
                                previous_message = message
                        elif previous_message and message.author != ctx.author:
                            messages.append(["Query: ", previous_message.content])
                            previous_message = None

                        if len(messages) >= limit or dt.now() > end_time:
                            break
                except discord.errors.Forbidden:
                    await ctx.send(f"Bot does not have 'Read Message History' permission in channel: {channel.name}")
                    continue
        if messages:
            messages.reverse()
            filename = self.save_messages_to_csv(key, messages)
            await ctx.send(f"Messages saved for user: {ctx.author}")
        else:
            await ctx.send("No messages found or an error occurred during scraping.")

        self.scraping_in_progress = False
        self.currently_scraping = None

        user = None
        if self.scraping_queue:
            next_ctx, next_key, next_client = self.scraping_queue.pop(0)
            await self.perform_scraping(next_ctx, next_key, next_client)
        return messages

    def load_messages_from_csv(self, key):
        safe_key = self._sanitize_key(key)
        filename = os.path.join(self.base_path, f'{safe_key}.csv')
        messages = []
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                messages = [row[1].lstrip(',').strip() for row in reader if row[0].strip() == "User:"]
        except FileNotFoundError:
            print(f"File does not exist: {filename}")
        except csv.Error as e:
            print(f"Error reading CSV file at line {reader.line_num}: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        return messages

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
        links_file = os.path.join(self.base_path, f'{safe_key}_links.txt')

        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

        with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w',
                                                                     encoding='utf-8') as outfile, open(links_file, 'w',
                                                                                                        encoding='utf-8') as linkfile:
            reader = csv.reader(infile)
            next(reader)  # Skip header
            conversation = []
            link_counter = 0
            for row in reader:
                if row[0].lower().startswith('query'):
                    if conversation:
                        outfile.write("\n".join(conversation) + "\n\n")
                    conversation = []
                if row[1].strip():
                    message = row[1].strip()
                    urls_in_message = url_pattern.findall(message)
                    for url in urls_in_message:
                        link_placeholder = f"link{link_counter}"
                        message = message.replace(url, link_placeholder)
                        linkfile.write(f"{link_placeholder},{url}\n")
                        link_counter += 1
                    conversation.append(message)
            if conversation:
                outfile.write("\n".join(conversation) + "\n")