from fastapi import FastAPI, HTTPException, Depends, Header
from cashu.wallet.wallet import Wallet
from cashu.wallet.db.memory import MemoryDatabase
import asyncio

app = FastAPI()

# API Key Authentication
API_KEYS = ["your_api_key_here"]  # Replace with actual key from Agent (AIDE)!

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key")

# Dictionary to store user wallets
user_wallets = {}

def get_user_wallet(user_id):
    if user_id not in user_wallets:
        wallet_db = MemoryDatabase()
        user_wallet = Wallet(db=wallet_db, mint_url="https://boardwalkcash.com")
        # Load the mint asynchronously
        asyncio.run(user_wallet.load_mint())
        user_wallets[user_id] = user_wallet
    return user_wallets[user_id]

# Endpoint for sending ecash
@app.post("/send")
async def send_ecash(user_id: str, amount: int, recipient_id: str, api_key: str = Depends(verify_api_key)):
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

        return {"status": "success", "token": token["token"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Endpoint for receiving ecash
@app.post("/receive")
async def receive_ecash(user_id: str, token: str, api_key: str = Depends(verify_api_key)):
    try:
        # Get the recipient's wallet
        recipient_wallet = get_user_wallet(user_id)
        # Add ecash to recipient's wallet
        await recipient_wallet.receive(token)
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Endpoint tot Check user wallet balance 
@app.post("/balance")
async def get_balance(user_id: str, api_key: str = Depends(verify_api_key)):
    try:
        wallet = get_user_wallet(user_id)
        balance = await wallet.balance()
        return {"available": balance.available, "pending": balance.pending}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))