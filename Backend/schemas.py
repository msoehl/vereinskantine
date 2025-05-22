from pydantic import BaseModel
from typing import List

class Product(BaseModel):
    id: int
    name: str
    price: float
    class Config:
        orm_mode = True

class ProductCreate(BaseModel):
    name: str
    price: float

class Transaction(BaseModel):
    user_id: int
    items: List[dict]

class TransactionOut(BaseModel):
    id: int
    user_id: int
    product_id: int
    timestamp: str
    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    username: str
    rfid: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    rfid: str
    class Config:
        orm_mode = True