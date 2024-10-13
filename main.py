from fastapi import FastAPI, HTTPException, Depends, Header
from cashu.wallet.wallet import Wallet
from cashu.core.db.memory import MemoryDatabase
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
        user_wallet = Wallet(url="https://boardwalkcash.com", db=wallet_db)
        asyncio.run(user_wallet.load_mint())
        user_wallets[user_id] = user_wallet
    return user_wallets[user_id]

# Endpoint for sending ecash
@app.post("/send")
async def send_ecash(user_id: str, amount: int, recipient_id: str, api_key: str = Depends(verify_api_key)):
    try:
        # Deduct ecash from sender's wallet
        token = await wallet.send(amount)
        
        # TODO: Transfer token to recipient (e.g., store in database)
        # For example, storing in a database associated with recipient_id

        return {"status": "success", "token": token}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint for receiving ecash
@app.post("/receive")
async def receive_ecash(user_id: str, token: str, api_key: str = Depends(verify_api_key)):
    try:
        # Add ecash to recipient's wallet
        await wallet.receive(token)
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

