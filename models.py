from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# User-Coin association table for many-to-many relationship
user_coins = Table(
    "user_coins",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("coin_id", Integer, ForeignKey("coins.id"))
)

class User(Base):
    """
    User model representing registered users in the system
    
    Attributes:
        id: Unique identifier for the user
        username: Unique username for login
        email: User's email address
        hashed_password: Securely stored password hash
        created_at: Account creation timestamp
        coins: Relationship to tracked coins
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with coins (many-to-many)
    coins = relationship("Coin", secondary=user_coins, back_populates="users")

class Coin(Base):
    """
    Coin model representing cryptocurrencies in the system
    
    Attributes:
        id: Unique identifier for the coin
        name: Full name of the cryptocurrency (e.g., "Bitcoin")
        symbol: Trading symbol (e.g., "BTC")
        users: Relationship to users tracking this coin
        prices: Relationship to historical price data
    """
    __tablename__ = "coins"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    symbol = Column(String, unique=True, index=True)
    
    # Relationship with users (many-to-many)
    users = relationship("User", secondary=user_coins, back_populates="coins")
    # Relationship with price history (one-to-many)
    prices = relationship("PriceHistory", back_populates="coin")

class PriceHistory(Base):
    """
    PriceHistory model for storing historical cryptocurrency prices
    
    Attributes:
        id: Unique identifier for the price entry
        coin_id: Foreign key to the associated coin
        price: Price in USD
        volume_24h: 24-hour trading volume (optional)
        change_24h: 24-hour price change percentage (optional)
        market_cap: Market capitalization (optional)
        timestamp: When this price was recorded
        coin: Relationship to the associated coin
    """
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id"))
    price = Column(Float)
    volume_24h = Column(Float, nullable=True)
    change_24h = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    coin = relationship("Coin", back_populates="prices")