from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import requests
from datetime import timedelta
from database import SessionLocal, engine, Base, get_db  # Import get_db from database.py
import crud, models, schemas, auth
from models import User

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Crypto Price Tracker API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

COINS = [
    {"name": "Bitcoin", "symbol": "btc", "id": "bitcoin"},
    {"name": "Ethereum", "symbol": "eth", "id": "ethereum"},
    {"name": "Cardano", "symbol": "ada", "id": "cardano"},
    {"name": "Solana", "symbol": "sol", "id": "solana"},
    {"name": "Binance Coin", "symbol": "bnb", "id": "binancecoin"},
    {"name": "XRP", "symbol": "xrp", "id": "ripple"},
    {"name": "Polkadot", "symbol": "dot", "id": "polkadot"},
    {"name": "Dogecoin", "symbol": "doge", "id": "dogecoin"},
    {"name": "Avalanche", "symbol": "avax", "id": "avalanche-2"},
    {"name": "Chainlink", "symbol": "link", "id": "chainlink"}
]

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Crypto Price Tracker API",
        "endpoints": [
            {"path": "/register", "method": "POST", "description": "Register a new user"},
            {"path": "/token", "method": "POST", "description": "Login to get access token"},
            {"path": "/users/me", "method": "GET", "description": "Get current user info"},
            {"path": "/users/coins", "method": "GET", "description": "Get coins tracked by current user"},
            {"path": "/users/coins/{coin_id}", "method": "POST", "description": "Add a coin to user's tracking list"},
            {"path": "/users/coins/{coin_id}", "method": "DELETE", "description": "Remove a coin from user's tracking list"},
            {"path": "/update", "method": "POST", "description": "Fetch and store the latest prices"},
            {"path": "/prices", "method": "GET", "description": "Retrieve the latest stored prices"},
            {"path": "/prices/{coin_name}", "method": "GET", "description": "View historical prices of a specific coin"},
            {"path": "/users/prices/{coin_name}", "method": "GET", "description": "View historical prices of a user's tracked coin"}
        ]
    }

# User registration and authentication
@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: User = Depends(auth.get_current_user)):
    return current_user

# User-coin management
@app.get("/users/coins")
def get_user_coins(current_user: User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return current_user.coins

@app.post("/users/coins/{coin_id}")
def add_coin_to_user(coin_id: int, current_user: User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    result = crud.add_coin_to_user(db, current_user.id, coin_id)
    if not result:
        raise HTTPException(status_code=404, detail="Coin not found")
    return {"status": "success", "message": "Coin added to user's tracking list"}

@app.delete("/users/coins/{coin_id}")
def remove_coin_from_user(coin_id: int, current_user: User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    result = crud.remove_coin_from_user(db, current_user.id, coin_id)
    if not result:
        raise HTTPException(status_code=404, detail="Coin not found or not in user's tracking list")
    return {"status": "success", "message": "Coin removed from user's tracking list"}

# Price update and retrieval
@app.post("/update")
def update_prices(db: Session = Depends(get_db)):
    """
    Update cryptocurrency prices from CoinGecko API
    
    Fetches current price data for all configured coins and stores it in the database.
    Returns a list of updated coin prices.
    """
    try:
        # Create comma-separated list of coin IDs for API request
        coin_ids = ",".join([coin["id"] for coin in COINS])
        
        # Configure API request parameters - only fetch price data
        price_params = {
            "ids": coin_ids,
            "vs_currencies": "usd"
        }
        
        # Add User-Agent header to avoid potential rate limiting
        headers = {
            "User-Agent": "Crypto Price Tracker API"
        }
        
        # Make request to CoinGecko API
        response = requests.get(COINGECKO_URL, params=price_params, headers=headers)
        
        # Check for successful response
        if response.status_code != 200:
            raise HTTPException(
                status_code=502, 
                detail=f"Failed to fetch from CoinGecko: {response.text}"
            )
        
        # Process response data
        prices = response.json()
        results = []
        
        # Process each coin
        for coin in COINS:
            name = coin["name"]
            symbol = coin["symbol"]
            coin_id = coin["id"]
            
            # Extract price data for this coin
            price_data = prices.get(coin_id, {})
            if not price_data or "usd" not in price_data:
                continue
                
            price = price_data.get("usd")
            
            # Get or create the coin in the database
            db_coin = crud.get_coin_by_name(db, name)
            if not db_coin:
                db_coin = crud.create_coin(db, schemas.CoinCreate(name=name, symbol=symbol))
                
            # Store price data in database
            price_entry = crud.add_price(db, db_coin, price)
            
            # Format timestamp for JSON response
            timestamp = price_entry.timestamp.isoformat() if hasattr(price_entry.timestamp, 'isoformat') else str(price_entry.timestamp)
            
            # Add to results
            results.append({
                "name": name,
                "symbol": symbol,
                "price": price_entry.price,
                "timestamp": timestamp
            })
        
        return {"status": "success", "data": results, "count": len(results)}
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while updating prices: {str(e)}"
        )

@app.get("/prices")
def get_latest_prices(db: Session = Depends(get_db)):
    return crud.get_latest_prices(db)

@app.get("/prices/{coin_name}")
def get_price_history(coin_name: str, db: Session = Depends(get_db)):
    history = crud.get_price_history(db, coin_name)
    if not history:
        raise HTTPException(status_code=404, detail="Coin not found or no price history")
    return history

@app.get("/users/prices/{coin_name}")
def get_user_price_history(
    coin_name: str, 
    current_user: User = Depends(auth.get_current_user), 
    db: Session = Depends(get_db)
):
    history = crud.get_user_price_history(db, current_user.id, coin_name)
    if not history:
        raise HTTPException(
            status_code=404, 
            detail="Coin not found, not tracked by user, or no price history"
        )
    return history