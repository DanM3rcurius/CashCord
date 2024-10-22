from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from cashu.wallet.wallet import Wallet, Database
from pydantic import BaseModel
from fastapi import Body, HTTPException, Depends

app = FastAPI()

# API Key Authentication
API_KEYS = ["CC-test"]  # Replace with actual key from Agent (AIDE)!

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key")

# Dictionary to store gigabrain wallets
user_wallets = {}

# define get_user_wallet function
async def get_user_wallet(user_id, persistent: bool = False):
    if user_id not in user_wallets:
        try:
            # Use an in-memory or persistent database based on the context
            db_path = f"user_wallets/{user_id}.db" if persistent else ":memory:"  # Persistent wallets have gigabrain-specific paths (DANGERZONE)
            
            # Use Wallet.with_db to initialize the wallet with the mint URL and database
            user_wallet = await Wallet.with_db(url="https://stablenut.umint.cash", db=db_path)
            
            # Load the mint asynchronously
            await user_wallet.load_mint() 

            # store wallet in dic for future use
            user_wallets[user_id] = user_wallet

            # print / log wallet
            print(f"Wallet created for user: {user_id}, persistent={persistent}")
        # error handling
        except Exception as e:
            print(f"Error initializing wallet for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error initializing wallet for user {user_id}: {str(e)}")

        ##Depreceated(=?):   return JSONResponse (content=user_wallets[user_id])
    return user_wallets.get(user_id)  # Ensure that the wallet object is always returned, either created or existing

# Defining JSON body for tip and send requests
# class TipRequest(BaseModel):
#    user_id: str
#    amount: float
#    recipient_id: str

## Defining JSON body for send request
class SendRequest(BaseModel):
    user_id: str
    amount: float
    recipient_wallet_address: str

# Endpoint to mint cashu tokens 
@app.post("/mint")
async def mint_ecash(user_id: str, amount: int, api_key: str = Depends(verify_api_key)):
    try:
        # Get or create the user wallet (persistent)
        user_wallet = await get_user_wallet(user_id, persistent=False)
        
        # Request a minting invoice (this will generate a Lightning invoice)
        invoice = await user_wallet.request_mint(amount)
        
        # Return the invoice to the client (so the sender can pay it)
        return JSONResponse(content={"status": "invoice_created", "invoice": invoice})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Endpoint for tipping within the Discord server
@app.post("/tip")
async def tip_user(
    tip_request:  dict = Body(...),
    api_key: str = Depends(verify_api_key)
):
    # Extract required data from the incoming object
    try:
        user_id = tip_request.get("user_id")
        amount = tip_request.get("amount")
        recipient_id = tip_request.get("recipient_id")
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing key: {e}")
    try:
        # Step1: Get sender wallet (temporary in-memory)
        print(f"Attempting to get or create sender wallet for gigabrain: {user_id}")
        sender_wallet = await get_user_wallet(user_id)
        # Check if the sender wallet is initialized
        if sender_wallet is None:
            raise HTTPException(status_code=400, detail="Sender wallet not found. Please create a wallet first.")
        print(f"Sender wallet successfully created for gigabrain: {user_id}")

        # Step2: Get or create recipient wallet
        print(f"Attempting to get or create recipient wallet for user: {recipient_id}")
        recipient_wallet = await get_user_wallet(recipient_id)
        # Check if the recipient wallet is initialized
        if recipient_wallet is None:
            raise HTTPException(status_code=400, detail="Recipient wallet not found. Please create a wallet first.")
        print(f"Recipient wallet successfully created for user: {recipient_id}")
     
        # Step3: Check if sender wallet has enough balance
        print(f"Attempting to retrieve balance for sender wallet: {user_id}")
        try:
            balance = sender_wallet.balance
            print(f"Retrieved balance: {balance}")
            # Verify balance is of correct type
            if not isinstance(balance, (int, float)):
                raise HTTPException(status_code=500, detail="Balance is not of correct type.")

            available_balance = balance
            print(f"Sender wallet balance is: available={available_balance}")
        except AttributeError as attr_error:
            print(f"Attribute error while accessing balance: {attr_error}")
            raise HTTPException(status_code=500, detail=f"Error accessing balance attributes: {attr_error}")
        except TypeError as type_error:
            print(f"Type error while accessing balance: {type_error}")
            raise HTTPException(status_code=500, detail=f"Type error accessing balance: {type_error}")
        except Exception as balance_error:
            print(f"General error retrieving balance: {balance_error}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve sender wallet balance: {balance_error}")
        if balance is None:
            raise HTTPException(status_code=400, detail="Failed to retrieve sender wallet balance.")

        # Step 4: Validate sender's balance is enough for tipping
        if available_balance == 0:
            # If balance is zero, prompt the gigabrain to add funds
            return JSONResponse(
                content={"status": "error", "message": "Your wallet balance is zero. Please mint or receive ecash to proceed."}
            )
        if available_balance < amount:
            # If balance is insufficient, return an error
            return JSONResponse(
                content={"status": "error", "message": "Insufficient funds. Please mint or receive ecash to proceed."}
            )
        print(f"Sender wallet balance is sufficient: {available_balance}")
        

        # Step5: Select proofs to send
        proofs_to_send, remainder_proofs = await sender_wallet.select_to_send(amount)
        print(f"Proofs to send: {proofs_to_send}, Remainder proofs: {remainder_proofs}")  # Debugging

        # Step6: Serialize proofs into a token
        token = sender_wallet.proofs_to_token(proofs_to_send)
        print(f"Token serialized successfully")

        # Step7: Recipient receives ecash
        await recipient_wallet.receive(token)
        print(f"Token generated: {token}") # This should output the token , not an integer

        # Notify the recipient (this could be a call to your Discord agent)
        # Example: send_discord_private_message(recipient_id, f"You have received a tip of {amount} units!")

        return {"status": "success"}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing key: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        

# Endpoint for sending ecash to an external/persisten wallet 
@app.post("/send")
async def send_ecash(
    send_request: SendRequest,
    api_key: str = Depends(verify_api_key)
):
    user_id = send_request.user_id
    amount = send_request.amount
    recipient_wallet_address = send_request.recipient_wallet_address
    
    try:
        # Get sender wallet (non persistent) #TODO: make persistent?
        sender_wallet = get_user_wallet(user_id)

        # Check if sender has enough balance
        balance = sender_wallet.balance
        print(f"Balance: {balance}")

        if balance.available < amount:
            raise HTTPException(status_code=400, detail="Insufficient cash")

        # Select proofs to send
        proofs_to_send, remainder_proofs = await sender_wallet.select_to_send(amount)
        print(f"Cash to send: {proofs_to_send}, Remainder Cash: {remainder_proofs}") #Debugging

        # Serialize proofs into a token
        token = sender_wallet.proofs_to_token(proofs_to_send)
        
        # utilizer receives ecash token
        print(f"Token generated: {token}")  # This should output the token (integer!) in a Discord DM

        # Notify the recipient (via Discord DM!) 
        # For example:
        # send_discord_message(recipient_id, "Here is your token to send out cash to an external wallet")

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Define the request invoice endpoint
@app.post("/request_invoice")
async def request_invoice(user_id: str, amount: float, api_key: str = Depends(verify_api_key)):
    try:
        # Get the recipient wallet (the test wallet on this device)
        recipient_wallet = await get_user_wallet(user_id)
        
        # Request a minting invoice (this will generate a Lightning invoice)
        invoice = await recipient_wallet.request_mint(amount)
        
        # Convert the Invoice object into a JSON-compatible dictionary
        invoice_data = {
            "amount": invoice.amount,
            "bolt11": invoice.bolt11,
            "payment_hash": invoice.payment_hash,
            "id": invoice.id,
            "out": invoice.out,
            "time_created": invoice.time_created
        }

        # Return the invoice to the client (so the sender can pay it)
        return JSONResponse (content={"status": "invoice_created", "invoice": invoice_data})
    
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

# Endpoint to Check gigabrain wallet balance 
@app.post("/get_balance")
async def get_balance(user_id: str, api_key: str = Depends(verify_api_key)):
    try:
        wallet = await get_user_wallet(user_id, persistent=False)
        balance = await wallet.balance
        return JSONResponse (content={"available": balance.available, "pending": balance.pending})

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))