from fastapi import FastAPI, Request, HTTPException
import stripe
import os
import sqlite3

app = FastAPI()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

DB_PATH = "/data/users.db"

# Vytvorenie databázy a tabuľky pri štarte
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
    print("✅ Databáza inicializovaná")

init_db()

@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
        print(f"✅ Event prijatý: {event['type']}")
    except Exception as e:
        print(f"❌ Signature error: {e}")
        raise HTTPException(status_code=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        metadata = session.metadata if hasattr(session, "metadata") else {}
        user_id_str = getattr(metadata, "telegram_user_id", None)
        
        print(f"🎉 Platba úspešná pre user_id: {user_id_str}")

        if user_id_str:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE users 
                    SET is_premium = 1 
                    WHERE user_id = ?
                """, (int(user_id_str),))
                
                # Ak používateľ ešte v DB nebol, vložíme ho
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO users (user_id, is_premium) 
                        VALUES (?, 1)
                    """, (int(user_id_str),))
                
                conn.commit()
                conn.close()
                print(f"✅ Prémiový prístup aktivovaný pre user {user_id_str}")
            except Exception as e:
                print(f"❌ Chyba databázy: {e}")

    return {"status": "success"}

@app.get("/")
async def health():
    return {"status": "webhook is running ✅"}
