from fastapi import FastAPI, HTTPException, Depends, Header JSONResponse
from cashu.wallet.wallet import Wallet, Database
from pydantic import BaseModel

app = FastAPI()

# API Key Authentication
API_KEYS = ["CC-test"]  # Replace with actual key from Agent (AIDE)!

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key")

# Dictionary to store user wallets
user_wallets = {}
# define get_user_wallet function
async def get_user_wallet(user_id):
    if user_id not in user_wallets:
        try:
            # init in memory db
            db_path = ":memory:" # Use an in-memory database for simplicity
            # Use Wallet.with_db to initialize the wallet with the mint URL and database
            user_wallet = await Wallet.with_db(url="https://stablenut.umint.cash", db=db_path)
            # Load the mint asynchronously
            await user_wallet.load_mint() 
            # store wallet in dic for future use
            user_wallets[user_id] = user_wallet
            # print / log wallet
            print(f"Wallet created for user: {user_id}")
        # error handling
        except Exception as e:
            print(f"Error initializing wallet for user {user_id}: {e}")
            raise
    return JSONResponse (content=user_wallets[user_id])

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
        sender_wallet = await get_user_wallet(user_id)
        recipient_wallet = await get_user_wallet(recipient_id)

        # Check if sender has enough balance
        balance = await sender_wallet.balance()
        print(f"Balance: {balance}")

        if balance.available < amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        # Select proofs to send
        proofs_to_send, remainder_proofs = await sender_wallet.select_to_send(amount)
        print(f"Proofs to send: {proofs_to_send}, Remainder proofs: {remainder_proofs}") #Debugging

        # Serialize proofs into a token
        token = sender_wallet.send_proofs(proofs_to_send)
        
        # Recipient receives ecash
        await recipient_wallet.receive(token) 
        print(f"Token generated: {token}")  # This should output the token, not an integer

        # Notify the recipient (this could be a call to your Discord agent)
        # For example:
        # send_discord_message(recipient_id, "You have received a tip of {} units!".format(amount))

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Define the request invoice endpoint
@app.post("/request_invoice")
async def request_invoice(user_id: str, amount: int, api_key: str = Depends(verify_api_key)):
    try:
        # Get the recipient wallet (the test wallet on this device)
        recipient_wallet = await get_user_wallet(user_id)
        
        # Request a minting invoice (this will generate a Lightning invoice)
        invoice = await recipient_wallet.request_mint(amount)
        
        # Return the invoice to the client (so the sender can pay it)
        return JSONResponse (content={"status": "invoice_created", "invoice": invoice})
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Define the check receive endpoint
@app.post("/receive")
async def check_receive(user_id: str, token: str, api_key: str = Depends(verify_api_key)):
    try:
        # Get the recipient wallet 
        recipient_wallet = await get_user_wallet(user_id)

        # Load proofs (receive tokens) from another wallet
        await recipient_wallet.load_proofs(token)

        print("Token received successfully!")
        return {"status": "success", "message": "Token received and ecash added to wallet"}
        return JSONResponse(content={"status": "success"})

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint to Check user wallet balance 
@app.post("/balance")
async def get_balance(user_id: str, api_key: str = Depends(verify_api_key)):
    try:
        wallet = await get_user_wallet(user_id)
        balance = await wallet.balance()
        return JSONResponse (content={"available": balance.available, "pending": balance.pending})

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))