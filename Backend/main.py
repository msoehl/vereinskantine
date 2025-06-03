from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db, engine
import models, schemas
from models import Product
from models import Transaction, TransactionItem
from datetime import datetime
import requests
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Webverzeichnis (gebautes Frontend)
web_path = "frontend"

# Assets mounten (CSS, JS, Bilder)
app.mount("/assets", StaticFiles(directory=os.path.join(web_path, "assets")), name="assets")

# index.html für /
@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(web_path, "index.html"))

# Optionaler Backend-Status-Endpunkt
@app.get("/status")
def read_status():
    return {"message": "Kantinen-Backend läuft"}

models.Base.metadata.create_all(bind=engine)

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


@app.put("/products/{id}")
def update_product(id: int, product: schemas.ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(Product).get(id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden")
    for attr, value in product.dict(exclude_unset=True).items():
        setattr(db_product, attr, value)
    db.commit()
    db.refresh(db_product)
    return db_product

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

@app.put("/users/{id}")
def update_user(id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).get(id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    for attr, value in user.dict(exclude_unset=True).items():
        setattr(db_user, attr, value)
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
        raise RuntimeError("Fehlende .env-Werte")

    token_response = requests.get(f"{base_url}/auth/accesstoken")
    accesstoken = token_response.text.strip()

    login_payload = {
        "accesstoken": accesstoken,
        "username": username,
        "password": hashlib.md5(password.encode()).hexdigest(),
        "appkey": appkey,
        "cid": cid
    }

    signin = requests.post(f"{base_url}/auth/signin", data=login_payload)

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
        if "VereinsKantine" not in roles:
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

@app.post("/sync/articles")
def sync_articles_from_vereinsflieger(db: Session = Depends(get_db)):
    
    base_url = "https://www.vereinsflieger.de/interface/rest"
    username = os.getenv("VFL_USERNAME")
    password = os.getenv("VFL_PASSWORD")
    appkey = os.getenv("VFL_APPKEY")
    cid = os.getenv("VFL_CID")    
    
    r = requests.get(f"{base_url}/auth/accesstoken")
    if r.status_code != 200:
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen des Accesstokens")
    accesstoken = accesstoken = r.text.strip()

    payload = {
        "accesstoken": accesstoken,
        "username": username,
        "password": hashlib.md5(password.encode()).hexdigest(),
        "appkey": appkey,
        "cid": cid
    }
    r = requests.post(f"{base_url}/auth/signin", data=payload)
    if r.status_code != 200:
        raise HTTPException(status_code=403, detail="Anmeldung fehlgeschlagen")

    r = requests.post(f"{base_url}/articles/list", data={"accesstoken": accesstoken})
    if r.status_code != 200:
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen der Artikel")
    articles = r.json()

    synced_count = 0
    for art in articles:
        if art.get("costtype") != "08800":
            continue
        name = art.get("designation")
        category = art.get("description")
        try:
            price = art["prices"][0]["unitprice"]
        except (IndexError, KeyError):
            continue

        existing = db.query(Product).filter_by(name=name).first()
        if existing:
            existing.price = price
            existing.category = category
        else:
            db.add(Product(name=name, price=price, category=category))
        synced_count += 1

    db.commit()
    return {"message": f"{synced_count} Artikel synchronisiert."}

