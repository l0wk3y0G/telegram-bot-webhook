from fastapi import FastAPI, Request, HTTPException
import stripe
import os
import json

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
        print(f"✅ Webhook event prijatý: {event['type']}")
    except Exception as e:
        print(f"❌ Webhook signature error: {e}")
        raise HTTPException(status_code=400)

    # Spracovanie platby
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        # Opravené načítanie metadata
        metadata = getattr(session, 'metadata', {})
        user_id = getattr(metadata, 'telegram_user_id', None) if metadata else None
        
        print(f"✅ Platba úspešná!")
        print(f"   User ID: {user_id}")
        print(f"   Session ID: {session.id}")
        print(f"   Amount: {getattr(session, 'amount_total', 'N/A')}")

    return {"status": "success"}


# Voliteľne - health check
@app.get("/")
async def health():
    return {"status": "bot webhook is running"}
