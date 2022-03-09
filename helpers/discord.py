from datetime import datetime
import discord

from .database import fetchLeaderboard, fetchUserPubKeys
from .generic import upload_to_hastebin, post_to_refractor
from .stellar import fetch_account_balance
from settings.default import BASE_FEE, USE_REFRACTOR

def hasRole(roles, REQUIRED_ROLE_ID):
    if discord.utils.get(roles, id=int(REQUIRED_ROLE_ID)):
        return True
    return False


def generate_payouts(conn):
    # possible bug if last_tx_date == None =>
    # counting all votes ever <--> this should only happen when account is new
    last_tx_date = fetch_last_tx()
    leaderboard_rows = fetchLeaderboard(conn, last_tx_date, datetime.now())
    user_rows = fetchUserPubKeys(conn)
    sumVotes = 0

    payoutUser = []

    for row in leaderboard_rows:
        pubKey = None

        for user in user_rows:
            if user[0] == row[0]:
                pubKey = user[1]

        if pubKey is not None:
            # user has public key
            sumVotes += row[1]
            payoutUser.append((row[0], row[1], pubKey))
        else:
            print(f"{row[0]} has no pub key connected to their account! They are missing out on {row[1]} upvotes :(")

    tx_cost = (BASE_FEE * len(payoutUser)) / 1000000

    pricepot = fetch_account_balance() - tx_cost

    if len(payoutUser) == 0:
        raise Exception("No eligible users this time!")
    if len(payoutUser) > 100:
        raise Exception(
            "Wow! There are a lot of eligible lumenauts (>100). We should upgrade our code to handle this case..."
        )
    payouts = []

    pricepot -= len(payoutUser)  # base reserve * 2 (2 claimaints for each claimableBalance)

    if pricepot <= 0:
        raise Exception(f"Balance of Pricepot is not high enough to support {len(payoutUser)} eligible lumenauts!")

    for user in payoutUser:
        payout = user[1] / sumVotes * pricepot
        payouts.append((user[2], payout))

    return payouts


def generate_report(payouts: list) -> str:
    tx_xdr = generate_reward_tx(payouts, BASE_FEE)

    if tx_xdr is None:
        raise Exception("Failed to load reward account!")

    return tx_xdr  # todo size limit?


async def notify_submitter(client, conn, user):
    notify_user = await client.fetch_user(user)
    try:
        payouts = generate_payouts(conn)
        report = generate_report(payouts)
        if USE_REFRACTOR:
            content = post_to_refractor(report)
        else:
            content = upload_to_hastebin(report)
    except Exception as e:
        content = f"```{e}```"
    await notify_user.send(content=f"New week, new lumenaut rewards:\n{content}")
