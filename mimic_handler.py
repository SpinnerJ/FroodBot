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
        self.use_ai = False
        self.ai_handler = AIHandler(base_path)
        self.current_mimic = None

    async def mimic_random(self, ctx):
        self.use_ai = False
        key = f'{ctx.author.name}_{ctx.guild.name}'
        self.current_mimic = key
        if key not in self.mimic_data:
            user_messages = self.data_handler.load_messages_from_csv(key)
            self.mimic_data[key] = user_messages
        await ctx.send(f"Now mimicking: {ctx.author.name}")

    async def clear(self, ctx):
        key = f'{ctx.author.name}_{ctx.guild.name}'
        if key in self.mimic_data:
            del self.mimic_data[key]
            if self.current_mimic == key:
                self.current_mimic = None
            await ctx.send("Cleared the current mimicked user.")
        else:
            await ctx.send("No user to clear. Use the !mimic_random or !mimic_ai command first.")

    async def r(self, ctx, *args):
        key = self.current_mimic
        if key in self.mimic_data:
            user_messages = self.mimic_data[key]
            if self.use_ai:
                input_text = ' '.join(args)
                generated_text = self.ai_handler.generate_response(input_text)
                await ctx.send(f"{key.split('_')[0]} says: {generated_text}")
            else:
                if user_messages:
                    await ctx.send(f"{key.split('_')[0]} says: {random.choice(user_messages)}")
                else:
                    await ctx.send(f"No messages found for user: {key.split('_')[0]}")
        else:
            await ctx.send("No user to mimic. Use the !mimic_random or !mimic_ai command first.")

    async def mimic_ai(self, ctx):
        self.use_ai = True
        key = f'{ctx.author.name}_{ctx.guild.name}'
        self.current_mimic = key
        if key not in self.mimic_data:
            user_messages = self.data_handler.load_messages_from_csv(key)
            self.mimic_data[key] = user_messages
        await ctx.send(f"Now mimicking with AI: {ctx.author.name}")

        model_path = os.path.join(self.ai_handler.base_path, key)
        if os.path.exists(model_path):
            await ctx.send(f"Found a trained model for user: {ctx.author.name}")
        else:
            training_thread = threading.Thread(target=self.ai_handler.preprocess_and_train, args=(key,))
            training_thread.start()
            await ctx.send(f"Training AI model for user: {ctx.author.name}")

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

        # Extract the username from the file name
        user_name = os.path.splitext(random_file)[0]  # remove the extension to get the username

        await ctx.send(f"Guess who said: {random_line}")
        await ctx.send(f"||{user_name}!||")