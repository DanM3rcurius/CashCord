# CashCord
a discord tipping bot for ecash


## install dependencies
``` bash
pip install fastapi uvicorn cashu
``` 

Thanks to [CashuBTC](https://github.com/cashubtc/nutshell) for their NutShell implementation.


## **Endpoints with Post requests**

### /send 
**Sending ecash (cashu)**
**request URL** `https://<ngrokURL>.ngrok-free.app/send`
```
curl -X 'POST' \
  'https://<ngrokURL>.ngrok-free.app/send' \
  -H 'accept: application/json' \
  -H 'x-api-key: CC-test' \
  -H 'Content-Type: application/json' \
  -d '{
  "user_id": "string",
  "amount": 0,
  "recipient_id": "string"
}'
```

### /request_invoice
**To receive ecash**
**Request URL** `https://<ngrokURL>.ngrok-free.app/request_invoice?user_id={user_id}&amount={amount}`

```
curl -X 'POST' \
  'https://<ngrokURL>.ngrok-free.app/request_invoice?user_id={user_id}&amount={amount}' \
  -H 'accept: application/json' \
  -H 'x-api-key: CC-test' \
  -d ''
```


### /receive
**To receive (load proofs) from another wallet**
**Request URL** `https://<ngrokURL>.ngrok-free.app/receive?user_id={userID}&token={token}`

```
curl -X 'POST' \
  'https://<ngrokURL>.ngrok-free.app/receive?user_id={user_id}&token={token}' \
  -H 'accept: application/json' \
  -H 'x-api-key: CC-test' \
  -d ''
```

### /balance
**To check balance of a users wallet**
**Request URL** `https://<ngrokURL>.ngrok-free.app/balance?user_id={user_id}`

```
curl -X 'POST' \
  'https://<ngrokURL>.ngrok-free.app/balance?user_id={user_id}' \
  -H 'accept: application/json' \
  -H 'x-api-key: CC-test' \
  -d ''
```
