from pydantic import BaseModel
from typing import List
from datetime import datetime

class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    category: str
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    price: float
    category: str


class ProductUpdate(BaseModel):
    name: str
    price: float
    category: str
    

class TransactionItem(BaseModel):
    product_id: int
    product_name: str
    price: float

class TransactionIn(BaseModel):
    user_id: int
    total: float
    items: List[TransactionItem]
    
class TransactionFull(BaseModel):
    id: int
    user_id: int
    username: str
    product_id: int
    product_name: str
    timestamp: datetime
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    rfid: str
    password: str

class UserUpdate(BaseModel):
    username: str
    rfid: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    rfid: str
    class Config:
        from_attributes = True