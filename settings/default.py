import environs
from stellar_sdk import Network

env = environs.Env()

env.read_env()

SQLITE3_ENABLED = env.bool("SQLITE3_ENABLED", True)
DATABASE_NAME = env.str("DATABASE_NAME", "accounts.db")

SENTRY_ENABLED = env.bool("SENTRY_ENABLED", False)
SENTRY_URL = env.str("SENTRY_URL", "")

STELLAR_USE_TESTNET = env.bool("STELLAR_USE_TESTNET", False)
STELLAR_ENDPOINT = "https://horizon-testnet.stellar.org" if STELLAR_USE_TESTNET else "https://horizon.stellar.org"
STELLAR_PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE if STELLAR_USE_TESTNET else Network.PUBLIC_NETWORK_PASSPHRASE
BASE_FEE = env.int("BASE_FEE", 10000)

USE_REFRACTOR = env.bool("USE_REFRACTOR", False)
DISCORD_BOT_TOKEN = env.str("DISCORD_BOT_TOKEN")

