from pydantic import BaseModel
from typing import List
from datetime import datetime
from typing import Optional

class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    category: str
    salestax: float
    vfl_articleid:str

    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    price: float
    category: str
    vfl_articleid:str
    salestax: float = 7.0


class ProductUpdate(BaseModel):
    name: str
    price: float
    category: str
    

class TransactionItem(BaseModel):
    product_id: int
    product_name: str
    price: float
    amount: int = 1

class TransactionIn(BaseModel):
    user_id: int
    total: float
    items: List[TransactionItem]
    vfl_enabled: Optional[bool] = False
    
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
    password: Optional[str] = None

class UserOut(BaseModel):
    id: int
    username: str
    rfid: str
    vf_uid: int
    class Config:
        from_attributes = True