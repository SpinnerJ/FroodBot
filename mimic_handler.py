from data_handler import DataHandler
import random
from ai_handler import AIHandler
import threading
import os
import csv


class MimicHandler:
    def __init__(self, data_handler, base_path):
        self.data_handler = data_handler
        self.mimic_data = {}
        self.use_ai = False  # Add a flag to keep track of the mimic mode
        self.ai_handler = AIHandler(base_path)  # Initialize AIHandler here

    async def mimic_random(self, ctx):
        self.use_ai = False  # Set the flag to False when mimicking randomly
        key = f'{ctx.author.name}_{ctx.guild.name}'
        messages = self.data_handler.load_messages_from_csv(key)
        user_messages = [msg[1] for msg in messages if msg[0] == "User message"]
        self.mimic_data[ctx.channel.id] = (ctx.author.name, user_messages)
        await ctx.send(f"Now mimicking: {ctx.author.name}")

    async def clear(self, ctx):
        if ctx.channel.id in self.mimic_data:
            del self.mimic_data[ctx.channel.id]
            await ctx.send("Cleared the current mimicked user.")
        else:
            await ctx.send("No user to clear. Use the !mimic_random or !mimic_ai command first.")

    async def r(self, ctx, *args):
        if ctx.channel.id in self.mimic_data:
            username, messages = self.mimic_data[ctx.channel.id]
            if self.use_ai:  # Use the flag to decide which method to use
                # Generate a response using AIHandler
                input_text = ' '.join(args)
                generated_text = self.ai_handler.generate_response(input_text)
                await ctx.send(f"{ctx.author.name} AI says: {generated_text}")
            else:
                # Generate a response by randomly selecting a message
                if messages:
                    await ctx.send(f"{username} says: {random.choice(messages)}")
                else:
                    await ctx.send(f"No messages found for user: {username}")
        else:
            await ctx.send("No user to mimic. Use the !mimic_random or !mimic_ai command first.")

    async def mimic_ai(self, ctx):
        if ctx.channel.id in self.mimic_data:
            username, messages = self.mimic_data[ctx.channel.id]
            key = self.data_handler._sanitize_key(username)
            self.data_handler.save_messages_to_csv(key, messages)

            # Create a new thread that runs the preprocess_and_train method
            training_thread = threading.Thread(target=self.ai_handler.preprocess_and_train, args=(key,))
            training_thread.start()

            await ctx.send(f"Training AI model for user: {username}")
        else:
            await ctx.send("No user to mimic. Use the !mimic_random or !mimic_ai command first.")

    async def guess_who(self, ctx):
        self.use_ai = False
        directory = "./data"
        files = [f for f in os.listdir(directory) if f.endswith('.csv')]  # get list of .csv files
        random_file = random.choice(files)  # choose a random .csv file
        file_path = os.path.join(directory, random_file)  # get the full file path

        # Read the .csv file and filter the lines labeled with "User message"
        with open(file_path, 'r', encoding='utf-8') as f:  # specify the encoding here
            reader = csv.reader(f)
            user_messages = [row[1] for row in reader if row[0] == "User message"]

        # Choose a random line from the filtered lines
        random_line = random.choice(user_messages) if user_messages else None

        # Extract the user name from the file name
        user_name = os.path.splitext(random_file)[0]  # remove the extension to get the username

        await ctx.send(f"Guess who said: {random_line}")
        await ctx.send(f"||{user_name}!||")


