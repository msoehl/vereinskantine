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
import json
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

# Optionaler Backend–Status-Endpunkt
@app.get("/status")
def read_status():
    return {"message": "Kantinen-Backend läuft"}

models.Base.metadata.create_all(bind=engine)

def get_vfl_token():
    base_url = "https://www.vereinsflieger.de/interface/rest"
    username = os.getenv("VFL_USERNAME")
    password = os.getenv("VFL_PASSWORD")
    appkey = os.getenv("VFL_APPKEY")
    cid = os.getenv("VFL_CID")

    print("[DEBUG] Lade VFL-Umgebungsvariablen...")
    if not all([username, password, appkey, cid]):
        raise Exception("[ERROR] Fehlende Vereinsflieger-Zugangsdaten (.env)")

    try:
        print("[DEBUG] Fordere Access-Token an...")
        r = requests.get(f"{base_url}/auth/accesstoken")
        r.raise_for_status()
        token = r.json().get("accesstoken")
        if not token:
            raise Exception("[ERROR] Kein Access-Token erhalten")
        print(f"[DEBUG] Access-Token erhalten: {token}")
    except Exception as e:
        print(f"[ERROR] Fehler beim Abrufen des Tokens: {e}")
        raise

    login_payload = {
        "accesstoken": token,
        "username": username,
        "password": hashlib.md5(password.encode()).hexdigest(),
        "appkey": appkey,
        "cid": cid
    }

    try:
        print("[DEBUG] Sende Login-Daten...")
        signin = requests.post(f"{base_url}/auth/signin", data=login_payload)
        print(f"[DEBUG] Login-Response-Code: {signin.status_code}")
        if signin.status_code != 200:
            raise Exception(f"[ERROR] Vereinsflieger-Login fehlgeschlagen: {signin.text}")
        
        signin_data = signin.json()
        updated_token = signin_data.get("accesstoken", token)
        print(f"[DEBUG] Login erfolgreich - verwendeter Token: {updated_token}")
    except Exception as e:
        print(f"[ERROR] Fehler beim Login: {e}")
        raise

    return updated_token

@app.post("/vfl-settings")
def set_vfl_enabled(setting: dict):
    with open("settings.json", "w") as f:
        json.dump(setting, f)
    return {"status": "ok"}

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

from collections import defaultdict

@app.post("/transaction")
def create_transaction(trans: schemas.TransactionIn, db: Session = Depends(get_db)):
    vflEnabled = trans.vfl_enabled
    from datetime import datetime
    import os
    import requests

    print("[DEBUG] Neue Transaktion wird erstellt")
    db_trans = Transaction(user_id=trans.user_id, total=trans.total, timestamp=datetime.utcnow())
    db.add(db_trans)
    db.commit()
    db.refresh(db_trans)
    print(f"[DEBUG] Transaktion ID {db_trans.id} gespeichert")

    db_user = db.query(models.User).filter(models.User.id == trans.user_id).first()
    vf_memberid = db_user.vf_memberid if db_user else None
    if vf_memberid:
        print(f"[DEBUG] Benutzer {db_user.username} mit vf_memberid={vf_memberid} gefunden")
    else:
        print("[WARNUNG] Kein Benutzer gefunden – Vereinsflieger-Verkauf wird übersprungen")

    accesstoken = get_vfl_token() if vflEnabled and vf_memberid else None
    if vflEnabled and not accesstoken:
        print("[ERROR] Kein gültiger Access-Token erhalten – VFL-Export wird deaktiviert.")
        vflEnabled = False

    # 🧮 Produkte nach ID aggregieren
    item_map = defaultdict(lambda: {"amount": 0, "item": None})
    for item in trans.items:
        item_map[item.product_id]["amount"] += item.amount
        item_map[item.product_id]["item"] = item  # nur letzter relevant für Metadaten

    for product_id, data in item_map.items():
        item = data["item"]
        total_amount = data["amount"]

        print(f"[DEBUG] Artikel {item.product_name} (ID {product_id}) wird gespeichert (x{total_amount})")
        db_item = TransactionItem(
            transaction_id=db_trans.id,
            product_id=product_id,
            product_name=item.product_name,
            price=item.price,
            amount=total_amount
        )
        db.add(db_item)

        if vflEnabled and vf_memberid:
            product = db.query(models.Product).filter(models.Product.id == product_id).first()
            price = product.price if product else item.price
            salestax = product.salestax if product and product.salestax is not None else float(os.getenv("VFL_TAX_RATE", 7))
            articleid = product.vfl_articleid if product and product.vfl_articleid else str(product_id)

            payload = {
                "accesstoken": accesstoken,
                "bookingdate": datetime.utcnow().date().isoformat(),
                "articleid": articleid,
                "amount": total_amount,
                "memberid": int(vf_memberid),
                "comment": f"Kantine Verkauf",
                "spid": int(os.getenv("VFL_SPHERE", 1)),
                "salestax": salestax
            }

            print(f"[DEBUG] Sende Verkauf an Vereinsflieger: {payload}")
            try:
                vf_response = requests.post("https://www.vereinsflieger.de/interface/rest/sale/add", json=payload)
                print(f"[DEBUG] Antwortcode: {vf_response.status_code}")
                if vf_response.status_code != 200:
                    print(f"[VFL-Fehler] {vf_response.text}")
            except Exception as e:
                print(f"[ERROR] API-Aufruf an Vereinsflieger fehlgeschlagen: {e}")

    db.commit()
    print("[DEBUG] Transaktion abgeschlossen")
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
    print("DEBUG: Starte Import von Vereinsflieger-Nutzern")

    base_url = "https://www.vereinsflieger.de/interface/rest"
    username = os.getenv("VFL_USERNAME")
    password = os.getenv("VFL_PASSWORD")
    appkey = os.getenv("VFL_APPKEY")
    cid = os.getenv("VFL_CID")

    print(f"DEBUG: env geladen: USER={username}, CID={cid}, APPKEY={appkey}")

    if not all([username, password, appkey, cid]):
        print("ERROR: Fehlende Umgebungsvariablen")
        raise HTTPException(status_code=500, detail="Fehlende .env-Werte")

    try:
        print("DEBUG: Fordere Access-Token an...")
        accesstoken= get_vfl_token()
        print(f"DEBUG: Access-Token erhalten: {accesstoken}")
    except Exception as e:
        print(f"ERROR: Fehler beim Access-Token: {e}")
        raise HTTPException(status_code=500, detail=f"Tokenfehler: {str(e)}")

    print("DEBUG: Hole Mitgliederliste...")
    member_response = requests.post(f"{base_url}/user/list", data={"accesstoken": accesstoken})
    print(f"DEBUG: Mitgliederliste-Response-Code: {member_response.status_code}")
    if member_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Mitgliederliste konnte nicht geladen werden")

    try:
        raw_data = member_response.json()
        print(f"DEBUG: JSON-Typ: {type(raw_data)}")
        if not isinstance(raw_data, dict):
            raise HTTPException(status_code=500, detail="Mitgliederliste ist kein Dictionary")
        members = list(raw_data.values())
        print(f"DEBUG: Mitglieder extrahiert: {len(members)}")
    except Exception as e:
        print(f"ERROR: JSON-Parsing: {e}")
        raise HTTPException(status_code=500, detail=f"JSON-Fehler in Mitgliederliste: {e}")

    created_users = []
    for m in members:
        if not isinstance(m, dict):
            print("WARN: Mitglied ist kein dict - übersprungen.")
            continue

        print(f"DEBUG: Verarbeite Mitglied: {m.get('firstname', '')} {m.get('lastname', '')}")

        roles = m.get("roles", [])
        if not isinstance(roles, list) or "VereinsKantine" not in roles:
            print("DEBUG: Rolle 'VereinsKantine' fehlt - übersprungen.")
            continue

        firstname = m.get("firstname", "").strip()
        lastname = m.get("lastname", "").strip()
        if not firstname or not lastname:
            print("DEBUG: Fehlender Vor-/Nachname - übersprungen.")
            continue

        username = f"{firstname} {lastname}"
        
        uid = m.get("uid")
        print(f"DEBUG: UID aus API: {uid}")

        if not uid:
            print(f"DEBUG: Kein UID gefunden für {username} - übersprungen.")
            continue    

        rfid = None
        key_entries = m.get("keymanagement", [])
        if isinstance(key_entries, list):
            for key in key_entries:
                if key.get("title") == "Schlüssel 2":
                    rfid_candidate = key.get("keyname") or key.get("rfidkey")
                    if rfid_candidate and str(rfid_candidate).strip():
                        rfid = str(rfid_candidate).strip()
                        print(f"DEBUG: RFID gefunden für {username}: {rfid}")
                        break

        if not rfid:
            print(f"DEBUG: Kein gültiger 'Schlüssel 2' für {username} - übersprungen.")
            continue

        if db.query(models.User).filter_by(username=username).first():
            print(f"DEBUG: Benutzer {username} existiert bereits - übersprungen.")
            continue  # <== fehlt aktuell!
        
        print(f"DEBUG: UID aus API: {m.get('uid')}")    
        print(f"DEBUG: Benutzer wird hinzugefügt: {username}")
        user = models.User(username=username, rfid=rfid, password=None, vf_memberid=m.get("memberid"))
        db.add(user)
        created_users.append(username)

    try:
        db.commit()
        print(f"DEBUG: Datenbank-Commit erfolgreich - {len(created_users)} Nutzer importiert.")
    except Exception as e:
        db.rollback()
        print("ERROR: Datenbankfehler beim Commit")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Datenbankfehler: {str(e)}")

    return {"imported": created_users}

@app.post("/sync/articles")
def sync_articles_from_vereinsflieger(db: Session = Depends(get_db)):
    print("DEBUG: Starte Artikel-Synchronisation...")
    
    base_url = "https://www.vereinsflieger.de/interface/rest"
    account = os.getenv("VFL_ACC")
    accesstoken = get_vfl_token()
    
    print("DEBUG: Hole Artikelliste...")
    r = requests.post(f"{base_url}/articles/list", data={"accesstoken": accesstoken})
    print(f"DEBUG: Artikel-Response-Code: {r.status_code}")
    if r.status_code != 200:
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen der Artikel")

    try:
        articles_raw = r.json()
        print(f"DEBUG: JSON-Typ der Antwort: {type(articles_raw)}")

        if isinstance(articles_raw, dict):
            if "articles" in articles_raw:
                articles = articles_raw["articles"]
                print(f"DEBUG: {len(articles)} Artikel im 'articles'-Key gefunden.")
            else:
                articles = [v for v in articles_raw.values() if isinstance(v, dict) and "designation" in v]
                print(f"DEBUG: {len(articles)} Artikel aus dict-Werten extrahiert.")
        elif isinstance(articles_raw, list):
            articles = articles_raw
            print(f"DEBUG: Antwort ist eine Liste mit {len(articles)} Artikeln.")
        else:
            raise ValueError(f"Unerwartete Struktur: {type(articles_raw)}")

    except Exception as e:
        print(f"ERROR: JSON-Verarbeitung fehlgeschlagen: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Verarbeiten der Artikeldaten: {e}")

    synced_count = 0
    for art in articles:
        if not isinstance(art, dict):
            print(f"WARN: Artikel ist kein dict: {art} - übersprungen.")
            continue

        print(f"DEBUG: Verarbeite Artikel: {art.get('designation')} (ID: {art.get('articleid')})")

        if art.get("account") != account:
            print(f"DEBUG: Sachkonto {art.get('account')} ist nicht {account} - übersprungen.")
            continue

        name = art.get("designation")
        category = art.get("description")
        
        try:
            price = art["prices"][0]["unitprice"]
        except (IndexError, KeyError, TypeError) as e:
            print(f"WARN: Preisfehler bei {name}: {e} - übersprungen.")
            continue

        existing = db.query(Product).filter_by(name=name).first()
        if existing:
            print(f"DEBUG: Aktualisiere bestehenden Artikel: {name}")
            existing.price = price
            existing.category = category
            existing.vfl_articleid = art.get("articleid")
        else:
            print(f"DEBUG: Neuer Artikel wird hinzugefügt: {name}")
            db.add(Product(name=name, price=price, category=category,salestax=art.get("prices")[0].get("salestax", 7),vfl_articleid=art.get("articleid")))

        synced_count += 1

    db.commit()
    print(f"DEBUG: Artikel-Synchronisation abgeschlossen - {synced_count} Artikel aktualisiert oder hinzugefügt.")
    return {"message": f"{synced_count} Artikel synchronisiert."}