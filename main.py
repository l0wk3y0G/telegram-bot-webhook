from fastapi import FastAPI, Request, HTTPException
import stripe
import os

app = FastAPI()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
        print(f"✅ Event: {event['type']}")
    except Exception as e:
        print(f"❌ Signature error: {e}")
        raise HTTPException(status_code=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        metadata = session.metadata if hasattr(session, "metadata") else {}
        user_id = getattr(metadata, "telegram_user_id", None)
        
        print("🎉 PLATBA ÚSPEŠNE PRIJATÁ!")
        print(f"   Telegram User ID: {user_id}")
        print(f"   Session ID: {getattr(session, 'id', 'N/A')}")
        print(f"   Amount: {getattr(session, 'amount_total', 'N/A')}")

        # Tu neskôr pridáme logiku na odomknutie prémií pre používateľa

    return {"status": "success"}

@app.get("/")
async def health():
    return {"status": "webhook is running ✅"}
