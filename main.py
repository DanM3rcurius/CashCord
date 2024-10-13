from fastapi import FastAPI, HTTPException
from cashu.wallet.wallet import Wallet
from fastapi import Depends, Header
import asyncio

app = FastAPI()

# API Key Authentication
API_KEYS = ["your_api_key_here"]  # Replace with actual key!

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key")

# Initialize the wallet outside of the endpoint functions
wallet = Wallet()
asyncio.run(wallet.load_mint("https://boardwalkcash.com/"))

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

