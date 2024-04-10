import discord
import pandas as pd
import spacy
from collections import Counter
from spacy.lang.en.stop_words import STOP_WORDS
from discord.ext import commands
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import Counter

# Download necessary spaCy model
nlp = spacy.load("en_core_web_sm")

bot = commands.Bot(command_prefix='~', intents=discord.Intents.all())


# Preprocess and analyze text
async def analyze_texts(messages):
    sia = SentimentIntensityAnalyzer()
    sentiment_scores = []
    topic_keywords = []

    for message in messages:
        doc = nlp(message.lower())
        lemmatized_tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
        sentiment_scores.append(sia.polarity_scores(' '.join(lemmatized_tokens)))
        topic_keywords.extend(
            [token.text for token in doc if token.pos_ in ['NOUN', 'PROPN'] and token.text not in STOP_WORDS])

    # Analyzing sentiment
    df = pd.DataFrame(sentiment_scores)
    emotional_spectrum = df.mean().to_dict()
    dominant_emotion = df.mean().idxmax()

    # Keyword extraction for topic identification
    topic_keywords_counts = Counter(topic_keywords)
    most_common_topics = topic_keywords_counts.most_common(5)  # Focus on top 5 for clarity

    # Highly positive/negative messages
    highly_positive = (df['compound'] > 0.5).mean()
    highly_negative = (df['compound'] < -0.5).mean()

    return emotional_spectrum, dominant_emotion, highly_positive, highly_negative, most_common_topics


@bot.event
async def on_ready():
    print("Bot ready!")


@bot.command(aliases=["at", "analyzetext"], help="Analyze the emotional tone, sentiment, and key topics in your "
                                                 "recent messages.")
async def analyze_text(ctx, limit: int = 2000):
    if not ctx.guild:
        await ctx.send("You must be in a server to use this command.")
        return

    messages = []
    for channel in ctx.guild.text_channels:
        if channel.permissions_for(ctx.guild.me).read_message_history:
            try:
                async for message in channel.history(limit=limit):
                    if message.author == ctx.author:
                        messages.append(message.content)
            except discord.Forbidden:
                continue

    emotional_spectrum, dominant_emotion, highly_positive, highly_negative, most_common_topics = await analyze_texts(
        messages)

    response = f"""
    Retrieved a sample of {len(messages)} messages. Here's the distilled insight:
    - Emotional Tone: Predominantly {dominant_emotion} with an emotional spectrum of {emotional_spectrum}.
    - Your dialogue trends towards a {highly_positive * 100:.2f}% positive and {highly_negative * 100:.2f}% negative sentiment.
    - Key Discussion Topics: {', '.join([word for word, count in most_common_topics])}.
    Krisrat
    """

    await ctx.send(response)


@bot.command(aliases=["ai", "analyzeimage"])
async def analyze_image(ctx):
    await ctx.send("Output3!")


# Ensure you handle the reading of the token more securely in production
with open("token.txt") as file:
    token = file.read()

bot.run(token)
