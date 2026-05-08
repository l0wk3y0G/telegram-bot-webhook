from fastapi import FastAPI, Request, HTTPException
import stripe
import os

app = FastAPI()

# Tieto kľúče nastavíme neskôr na Renderi
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
    except Exception:
        raise HTTPException(status_code=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("telegram_user_id")
        print(f"✅ Platba úspešná pre používateľa: {user_id}")

    return {"status": "success"}
