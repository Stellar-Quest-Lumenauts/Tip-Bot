import discord
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option
import sentry_sdk

from helpers.stellar import validate_pub_key, check_if_exchange
from helpers.discord import hasRole, notify_submitter
from helpers.database import   linkUserPubKey, setup_db, create_connection, getUserPubKey
from settings.default import (
    SENTRY_ENABLED,
    SENTRY_URL,
    DATABASE_NAME,
    DISCORD_BOT_TOKEN,
)

if SENTRY_ENABLED:
    sentry_sdk.init(SENTRY_URL, traces_sample_rate=1.0)

intents = discord.Intents(reactions=True, messages=True)
client = discord.Client(intents=intents)
slash = SlashCommand(client, sync_commands=True)
conn = create_connection(DATABASE_NAME)


async def processTip(amount, author, backer):
    """
    This function is called when a user wants to send a tip to another user
    """
    # Get Both the backers, and User's public key
    public_key_backer = getUserPubKey(conn, backer)
    public_key_author = getUserPubKey(conn, author.id)

    # Verify both accounts exist
    if public_key_backer is None:
        return f"You have attempted to tip a user but you have not linked your Stellar account. Please use `/link` to link your account."
    if public_key_author is None:
        await author.send(f"<@{backer}> attempted to tip you with {amount} 🐻 but you have not linked your Stellar account. Please use `/link` to link your account.")
        return f"{author} is not registered! They have been notiified"

    # Check if the user has enough balance
    if fetch_account_balance(public_key_backer) - float(amount) < 0:
        return f"You do not have enough balance to tip <@{backer}> {amount} 🐻"   

    # Generate XDR
    xdr = generate_payment(public_key_backer, public_key_author, amount)

    return f"{xdr}"

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

@client.event
async def on_reaction_add(reaction, user):
    if(
        user.id != reaction.message.author.id
        and user.id != client.user.id
    ):
        if str(reaction.emoji) == "🐻‍❄️":
            await user.send(await processTip(100, reaction.message.author, user.id))
        if str(reaction.emoji) == "🐻":
            await user.send(await processTip(10, reaction.message.author, user.id))
        elif str(reaction.emoji) == "🐼":
            await user.send(await processTip(5, reaction.message.author, user.id))
        elif str(reaction.emoji) == "🧸":
            await user.send(await processTip(1, reaction.message.author, user.id))



@slash.slash(
    name="link",
    description="Link your public key",
    options=[
        create_option(
            name="public_key",
            description="public-net public key",
            option_type=3,
            required=True,
        )
    ],
)
async def _link_reward(ctx, public_key: str):
    if not validate_pub_key(public_key):
        await ctx.send("Invalid public key supplied!")
    else:
        if not check_if_exchange(public_key):
            if linkUserPubKey(conn, ctx.author_id, public_key):
                await ctx.send(f"Linked `{public_key}` to your discord account!")
            else:
                await ctx.send("Unknown error linking your public key! Please ask somewhere...")
        else:
            await ctx.send("The provided public key belongs to an exchange! Please create a Stellar account that you have access to control.")

@slash.slash(
    name="my_public_key",
    description="Display your public key",
)
async def _my_pub_key(ctx):
    public_key = getUserPubKey(conn, ctx.author_id)

    if public_key is not None:
        await ctx.send(f"Your account is associated with the following public_key {public_key}")
    else:
        await ctx.send("Your account has not been found. Use `/link public_key` to add it to the database.")


if __name__ == "__main__":
    setup_db(conn)
    client.run(DISCORD_BOT_TOKEN)
