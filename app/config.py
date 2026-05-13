import os

from dotenv import load_dotenv

load_dotenv(".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
BILLING_DAY = int(os.getenv("BILLING_DAY", 15))

DEFAULT_PRICE = os.getenv("PRICE", "0")
DEFAULT_PAYMENT_INFO = os.getenv("PAYMENT_INFO", "—")
