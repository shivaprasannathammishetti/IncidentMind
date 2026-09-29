import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("HINDSIGHT_API_KEY")
BASE_URL = os.getenv("HINDSIGHT_BASE_URL")
BANK_ID = os.getenv("HINDSIGHT_BANK_ID")

print(f"Bank: {BANK_ID}")
print("⚠️ This will permanently delete ALL memories in this bank.")
print("The bank itself will remain.")

confirm = input("\nType CLEAR to continue: ")

if confirm == "CLEAR":

    url = f"{BASE_URL}/v1/default/banks/{BANK_ID}/memories"

    response = requests.delete(
        url,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Accept": "application/json"
        }
    )

    print("\nStatus:", response.status_code)
    print("Response:", response.text)

    if response.status_code == 200:
        print("\n✅ All memories cleared successfully!")
    else:
        print("\n❌ Clearing failed. Nothing else was changed.")

else:
    print("\n❌ Cancelled.")