from fastapi import FastAPI, Request, HTTPException
import stripe
import os
import sqlite3

app = FastAPI()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

DB_PATH = "/data/users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            messages INTEGER DEFAULT 0,
            is_premium INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Database initialized")

init_db()

@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
        print(f"✅ Event: {event['type']}")
    except Exception as e:
        print(f"❌ Signature error: {e}")
        raise HTTPException(status_code=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = getattr(session, 'metadata', None)
        
        user_id = getattr(metadata, 'telegram_user_id', None)
        print(f"🔍 User ID from metadata: {user_id}")

        if user_id:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO users (user_id, is_premium)
                    VALUES (?, 1)
                    ON CONFLICT(user_id) DO UPDATE SET is_premium = 1
                """, (int(user_id),))
                
                conn.commit()
                conn.close()
                print(f"🎉 PREMIUM SUCCESSFULLY ACTIVATED for user {user_id}")
            except Exception as e:
                print(f"❌ DB Error: {e}")

    return {"status": "success"}

@app.get("/")
async def health():
    return {"status": "webhook running ✅"}
