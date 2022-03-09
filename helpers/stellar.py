import time
from datetime import datetime
from typing import Union
from stellar_sdk import TransactionBuilder, Server, Keypair, Asset
from stellar_sdk.operation.create_claimable_balance import Claimant
import requests
import json

from settings.default import (
    STELLAR_USE_TESTNET,
    STELLAR_ENDPOINT,
    STELLAR_PASSPHRASE,
    BASE_FEE,
)

if STELLAR_USE_TESTNET:
    print("Using stellar testnet")

server = Server(horizon_url=STELLAR_ENDPOINT)


def fetch_account_balance(pubKey: str) -> float:
    """
    Returns the balance of the given account available to be send
    """
    try:
        acc = server.accounts().account_id(pubKey).call()
    except Exception as e:
        print(f"Specified account ({pubKey}) does not exists:", e)
        return 0

    for b in acc["balances"]:
        if b["asset_type"] == "native":
            balance = float(b["balance"])
            return balance
            
    return -1

def generate_payment(source_account: str, destination_account: str, amount: str) -> str:
    base_fee = server.fetch_base_fee()
    stellar_account = server.load_account(source_account)

    transaction = (
        TransactionBuilder(
            source_account=stellar_account,
            network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
            base_fee=base_fee,
        )
    )

    if fetch_account_balance(destination_account) == -1:
        transaction.append_create_claimable_balance_op(
            asset=Asset.native(), # TODO: Temporary
            claimants=[Claimant(destination_account), Claimant(source_account)],
            amount=amount,
        )
    else:
        transaction.append_payment_op(
            destination=destination_account, 
            amount=amount,
            asset_code="XLM", # TODO: Temporary
        )

    transaction.build()
    return transaction.to_xdr()

def validate_pub_key(pub_key: str) -> bool:
    """
    Valids a public key
    Returns true if valid key
    """
    try:
        Keypair.from_public_key(pub_key)
        return True
    except Exception:
        return False

def check_if_exchange(pub_key: str) -> bool:
    """
    Checks if the given public key is an exchange
    Returns true if exchange
    """
    url = f"https://api.stellar.expert/explorer/directory/{pub_key}"
    try:
        request = requests.get(url)

        if request.status_code == 404:
            return False

        data = json.loads(request.text)

        if data == {}:
            return False

        print(data)

        if "exchange" in data["tags"]:
            return True

    except Exception as e:
        print(e)
        print("Failed to fetch exchange info from stellar.expert")
    #return False
