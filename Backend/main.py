from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from database import get_db
from database import SessionLocal, engine
import models, schemas

from sqlalchemy.orm import Session

app = FastAPI()

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
def get_products():
    db = SessionLocal()
    return db.query(models.Product).all()

@app.post("/products", response_model=schemas.ProductCreate)
def create_product(prod: schemas.ProductCreate):
    db = SessionLocal()
    db_item = models.Product(**prod.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/transactions", response_model=list[schemas.TransactionFull])
def get_transactions():
    db = SessionLocal()
    transactions = db.query(models.Transaction).all()
    results = []
    for t in transactions:
        product = db.query(models.Product).filter(models.Product.id == t.product_id).first()
        user = db.query(models.User).filter(models.User.id == t.user_id).first()
        results.append({
            "id": t.id,
            "timestamp": t.timestamp,
            "user_id": t.user_id,
            "username": user.username if user else "Unbekannt",
            "product_id": t.product_id,
            "product_name": product.name if product else "Unbekannt"
        })
    return results
@app.post("/transaction")
def record_transaction(trans: schemas.TransactionIn):
    db = SessionLocal()
    for item in trans.items:
        db_item = models.Transaction(user_id=trans.user_id, product_id=item.product_id)
    db.add(db_item)
    db.commit()
    return {"message": "Transaktion gespeichert"}

@app.get("/users", response_model=list[schemas.UserOut])
def get_users():
    db = SessionLocal()
    return db.query(models.User).all()

@app.post("/users", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate):
    db = SessionLocal()
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login")
def login(user: schemas.UserCreate):
    db = SessionLocal()
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
