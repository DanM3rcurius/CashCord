from fastapi import FastAPI, HTTPException, Depends, Header
from cashu.wallet.wallet import Wallet, Database
from pydantic import BaseModel

import asyncio

app = FastAPI()

# API Key Authentication
API_KEYS = ["CC-test"]  # Replace with actual key from Agent (AIDE)!

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key")

# Dictionary to store user wallets
user_wallets = {}

def get_user_wallet(user_id):
    if user_id not in user_wallets:
        # init in memory db
        wallet_db = Database(db_name=":memory:", db_location=":memory:")
        # init wallet w/o mint url
        user_wallet = Wallet(db=wallet_db, url="https://stablenut.umint.cash")
        # Load the mint asynchronously
        asyncio.run(user_wallet.load_mint("https://stablenut.umint.cash"))
        # store init wallet for user
        user_wallets[user_id] = user_wallet
    return user_wallets[user_id]

## defining json body
class SendRequest(BaseModel):
    user_id: str
    amount: int
    recipient_id: str

# Endpoint for sending and automatically receiving ecash
@app.post("/send")
async def send_ecash(
    send_request: SendRequest,
    api_key: str = Depends(verify_api_key)
):
    user_id = send_request.user_id
    amount = send_request.amount
    recipient_id = send_request.recipient_id
    try:
        sender_wallet = get_user_wallet(user_id)
        recipient_wallet = get_user_wallet(recipient_id)

        # Check if sender has enough balance
        balance = await sender_wallet.balance()
        if balance.available < amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        # Sender sends ecash
        token = await sender_wallet.send(amount)

        # Recipient receives ecash
        await recipient_wallet.receive(token["token"])

        # Notify the recipient (this could be a call to your Discord agent)
        # For example:
        # send_discord_message(recipient_id, "You have received a tip of {} units!".format(amount))

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# Endpoint to Check user wallet balance 
@app.post("/balance")
async def get_balance(user_id: str, api_key: str = Depends(verify_api_key)):
    try:
        wallet = get_user_wallet(user_id)
        balance = await wallet.balance()
        return {"available": balance.available, "pending": balance.pending}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))