from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import get_db, engine
import models, schemas
from models import Transaction, TransactionItem
from datetime import datetime
import requests
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

#app.mount("/", StaticFiles(directory="Frontend", html=True), name="static")

origins = [
    "http://localhost:3000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Kantinen-Backend läuft"}

@app.get("/products", response_model=list[schemas.ProductOut])
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

@app.post("/products", response_model=schemas.ProductCreate)
def create_product(prod: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_item = models.Product(**prod.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    transactions = db.query(Transaction).all()
    result = []
    for t in transactions:
        items = db.query(TransactionItem).filter(TransactionItem.transaction_id == t.id).all()
        result.append({
            "id": t.id,
            "user_id": t.user_id,
            "total": t.total,
            "timestamp": t.timestamp,
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "price": item.price
                } for item in items
            ]
        })
    return result

@app.post("/transaction")
def create_transaction(trans: schemas.TransactionIn, db: Session = Depends(get_db)):
    db_trans = Transaction(user_id=trans.user_id, total=trans.total, timestamp=datetime.utcnow())
    db.add(db_trans)
    db.commit()
    db.refresh(db_trans)

    for item in trans.items:
        db_item = TransactionItem(
            transaction_id=db_trans.id,
            product_id=item.product_id,
            product_name=item.product_name,
            price=item.price
        )
        db.add(db_item)

    db.commit()
    return {"message": "Transaktion gespeichert", "transaction_id": db_trans.id}

@app.get("/users", response_model=list[schemas.UserOut])
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.post("/users", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login")
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter_by(username=user.username).first()
    if db_user and db_user.password == user.password:
        return {"status": "ok"}
    raise HTTPException(status_code=401, detail="Login fehlgeschlagen")

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
        return {"message": "Produkt gelöscht"}
    else:
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden")

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return {"message": "Benutzer gelöscht"}
    else:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")

@app.post("/import-users")
def import_users_from_vereinsflieger(db: Session = Depends(get_db)):
    base_url = "https://www.vereinsflieger.de/interface/rest"
    username = os.getenv("VFL_USERNAME")
    password = os.getenv("VFL_PASSWORD")
    appkey = os.getenv("VFL_APPKEY")
    cid = os.getenv("VFL_CID")

    if not all([username, password, appkey, cid]):
        print("FEHLER: Eine oder mehrere .env-Werte fehlen.")
        print("VFL_USERNAME:", username)
        print("VFL_PASSWORD:", "gesetzt" if password else "FEHLT")
        print("VFL_APPKEY:", appkey)
        print("VFL_CID:", cid)
        raise RuntimeError("Fehlende .env-Werte")

    token_response = requests.get(f"{base_url}/auth/accesstoken")
    accesstoken = token_response.text.strip()

    print("AccessToken:", accesstoken)

    login_payload = {
        "accesstoken": accesstoken,
        "username": username,
        "password": hashlib.md5(password.encode()).hexdigest(),
        "appkey": appkey,
        "cid": cid
    }

    print("📦 Login Payload (ohne Passwort):", {k: v for k, v in login_payload.items() if k != "password"})

    signin = requests.post(f"{base_url}/auth/signin", data=login_payload)

    print("📡 Signin Status:", signin.status_code)
    print("📨 Signin Response:", signin.text)

    if signin.status_code != 200:
        raise HTTPException(status_code=401, detail="Anmeldung fehlgeschlagen")

    member_response = requests.post(
        f"{base_url}/user/list", data={"accesstoken": accesstoken}
    )
    if member_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Mitgliederliste konnte nicht geladen werden")

    members = member_response.json()
    created_users = []

    for m in members:
        roles = [r.get("role") for r in m.get("roles", [])]
        if "Clubfridge" not in roles:
            continue

        if "firstname" in m and "lastname" in m:
            username = f"{m['firstname']} {m['lastname']}".strip()

            rfid = None
            key_entries = m.get("keymanagement", [])
            for key in key_entries:
                if key.get("label") == "Schlüssel 2":
                    rfid = key.get("value")
                    break

            existing = db.query(models.User).filter_by(username=username).first()
            if not existing:
                user = models.User(username=username, rfid=rfid, password=None)
                db.add(user)
                created_users.append(username)

    db.commit()
    return {"imported": created_users}