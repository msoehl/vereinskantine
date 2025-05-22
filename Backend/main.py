from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import SessionLocal, engine
import models, schemas

from sqlalchemy.orm import Session

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Kantinen-Backend läuft"}

@app.get("/products", response_model=list[schemas.Product])
def get_products():
    db = SessionLocal()
    return db.query(models.Product).all()

@app.post("/products", response_model=schemas.Product)
def create_product(prod: schemas.ProductCreate):
    db = SessionLocal()
    db_item = models.Product(**prod.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/transactions", response_model=list[schemas.TransactionOut])
def get_transactions():
    db = SessionLocal()
    return db.query(models.Transaction).all()

@app.post("/transaction")
def record_transaction(trans: schemas.Transaction):
    db = SessionLocal()
    for item in trans.items:
        db_item = models.Transaction(user_id=trans.user_id, product_id=item["product_id"])
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