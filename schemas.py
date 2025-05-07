from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

class PriceHistoryBase(BaseModel):
    price: float
    volume_24h: Optional[float] = None
    change_24h: Optional[float] = None
    market_cap: Optional[float] = None
    timestamp: datetime

    class Config:
        orm_mode = True

class CoinBase(BaseModel):
    name: str
    symbol: str

class CoinCreate(CoinBase):
    pass

class Coin(CoinBase):
    id: int
    prices: List[PriceHistoryBase] = []

    class Config:
        orm_mode = True

class PriceHistory(PriceHistoryBase):
    id: int
    coin_id: int

# Add these new user-related schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(UserBase):
    id: int
    created_at: datetime
    coins: List[CoinBase] = []

    class Config:
        orm_mode = True