from sqlalchemy.orm import Session
from models import Coin, PriceHistory, User
from schemas import CoinCreate, UserCreate
from datetime import datetime
from auth import get_password_hash, verify_password
from database import get_db  # Import from database.py

# User operations
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# User-coin operations
def add_coin_to_user(db: Session, user_id: int, coin_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    coin = db.query(Coin).filter(Coin.id == coin_id).first()
    if not user or not coin:
        return None
    user.coins.append(coin)
    db.commit()
    return {"user_id": user_id, "coin_id": coin_id}

def remove_coin_from_user(db: Session, user_id: int, coin_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    coin = db.query(Coin).filter(Coin.id == coin_id).first()
    if not user or not coin:
        return None
    user.coins.remove(coin)
    db.commit()
    return {"user_id": user_id, "coin_id": coin_id}

def get_user_coins(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    return user.coins

# Coin operations
def get_coin_by_name(db: Session, name: str):
    return db.query(Coin).filter(Coin.name == name).first()

def get_all_coins(db: Session):
    return db.query(Coin).all()

def create_coin(db: Session, coin: CoinCreate):
    db_coin = Coin(name=coin.name, symbol=coin.symbol)
    db.add(db_coin)
    db.commit()
    db.refresh(db_coin)
    return db_coin

def add_price(db: Session, coin: Coin, price: float):
    """
    Add a new price entry for a coin
    
    Args:
        db: Database session
        coin: Coin object to add price for
        price: Current price in USD
        
    Returns:
        The created PriceHistory object
    """
    db_price = PriceHistory(
        coin_id=coin.id,
        price=price
    )
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price

def get_latest_prices(db: Session):
    coins = db.query(Coin).all()
    result = []
    for coin in coins:
        latest = db.query(PriceHistory).filter(PriceHistory.coin_id == coin.id).order_by(PriceHistory.timestamp.desc()).first()
        if latest:
            result.append({"name": coin.name, "symbol": coin.symbol, "price": latest.price, "timestamp": latest.timestamp})
    return result

def get_price_history(db: Session, coin_name: str):
    coin = get_coin_by_name(db, coin_name)
    if not coin:
        return []
    return db.query(PriceHistory).filter(PriceHistory.coin_id == coin.id).order_by(PriceHistory.timestamp.desc()).all()

def get_user_price_history(db: Session, user_id: int, coin_name: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    
    coin = get_coin_by_name(db, coin_name)
    if not coin:
        return []
    
    # Check if user is tracking this coin
    if coin not in user.coins:
        return []
    
    return db.query(PriceHistory).filter(PriceHistory.coin_id == coin.id).order_by(PriceHistory.timestamp.desc()).all()