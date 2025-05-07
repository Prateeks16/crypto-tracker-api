import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# API URL configuration
API_URL = "http://127.0.0.1:8000"

# Page configuration
st.set_page_config(
    page_title="Crypto Price Tracker Dashboard",
    page_icon="📈",
    layout="wide"
)

# ----- AUTHENTICATION FUNCTIONS -----

def login():
    """Handle user login and authentication"""
    with st.sidebar:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            response = requests.post(
                f"{API_URL}/token",
                data={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                st.session_state["token"] = token_data["access_token"]
                st.success("Login successful!")
                st.rerun()
                return True
            else:
                st.error("Invalid username or password")
                return False
        
        if st.button("Register"):
            st.session_state["page"] = "register"
            return False
    
    return False

def register():
    """Handle new user registration"""
    with st.sidebar:
        st.title("Register")
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Register"):
            response = requests.post(
                f"{API_URL}/register",
                json={"username": username, "email": email, "password": password}
            )
            
            if response.status_code == 200:
                st.success("Registration successful! Please login.")
                st.session_state["page"] = "login"
                return False
            else:
                st.error(f"Registration failed: {response.text}")
                return False
        
        if st.button("Back to Login"):
            st.session_state["page"] = "login"
            return False
    
    return False

# ----- API INTERACTION FUNCTIONS -----

def get_user_coins():
    """Fetch coins tracked by the current user"""
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    response = requests.get(f"{API_URL}/users/coins", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch user's coins")
        return []

def get_all_coins():
    """Fetch all available coins and their current prices"""
    try:
        response = requests.get(f"{API_URL}/prices")
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch available coins: Status {response.status_code}, Response: {response.text}")
            return []
    except Exception as e:
        st.error(f"Exception when fetching coins: {str(e)}")
        return []

def get_price_history(coin_name):
    """Fetch historical price data for a specific coin"""
    headers = {}
    if "token" in st.session_state:
        headers = {"Authorization": f"Bearer {st.session_state['token']}"}
        response = requests.get(f"{API_URL}/users/prices/{coin_name}", headers=headers)
        
        if response.status_code != 200:
            # Fall back to public endpoint
            response = requests.get(f"{API_URL}/prices/{coin_name}")
    else:
        response = requests.get(f"{API_URL}/prices/{coin_name}")
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch price history for {coin_name}")
        return []

def add_coin_to_tracking(coin_id):
    """Add a coin to the user's tracking list"""
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    
    # Debug the coin_id being passed
    st.write(f"Debug - Adding coin with ID: {coin_id}")
    
    # If coin_id is not numeric, try to find the coin by name in the database
    try:
        # Try to convert to int if it's a numeric string
        if isinstance(coin_id, str) and coin_id.isdigit():
            coin_id = int(coin_id)
    except:
        pass
        
    response = requests.post(f"{API_URL}/users/coins/{coin_id}", headers=headers)
    
    if response.status_code == 200:
        st.success("Coin added to tracking list!")
        return True
    else:
        st.error(f"Failed to add coin to tracking list: {response.text}")
        return False

def remove_coin_from_tracking(coin_id):
    """Remove a coin from the user's tracking list"""
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    response = requests.delete(f"{API_URL}/users/coins/{coin_id}", headers=headers)
    
    if response.status_code == 200:
        st.success("Coin removed from tracking list!")
        return True
    else:
        st.error("Failed to remove coin from tracking list")
        return False

def update_prices():
    """Update cryptocurrency prices from the API"""
    try:
        response = requests.post(f"{API_URL}/update")
        
        if response.status_code == 200:
            result = response.json()
            count = result.get("count", 0)
            st.success(f"Prices updated successfully! Updated {count} coins.")
            return True
        else:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_detail = error_data["detail"]
            except:
                error_detail = response.text
                
            st.error(f"Failed to update prices: {error_detail}")
            return False
    except Exception as e:
        st.error(f"Exception occurred: {str(e)}")
        return False

# ----- DASHBOARD UI FUNCTIONS -----

def show_dashboard():
    """Display the main dashboard UI"""
    st.title("Crypto Price Tracker Dashboard")
    
    # Sidebar options
    with st.sidebar:
        st.title("Options")
        
        if st.button("Update Prices"):
            update_prices()
        
        if "token" in st.session_state:
            if st.button("Logout"):
                del st.session_state["token"]
                st.rerun()
    
    # Get cryptocurrency data
    all_coins = get_all_coins()
    
    if not all_coins:
        st.warning("No price data available. Please update prices.")
        return
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(all_coins)
    
    # ----- CURRENT PRICES SECTION -----
    st.header("Current Prices")
    
    # Create three columns for better layout
    col1, col2, col3 = st.columns(3)
    
    # Display metrics in columns
    for i, coin in enumerate(all_coins):
        col = [col1, col2, col3][i % 3]
        with col:
            price_change = coin.get("change_24h", 0)
            delta_color = "normal"
            if price_change:
                delta_color = "inverse" if price_change < 0 else "normal"
            
            st.metric(
                f"{coin['name']} ({coin['symbol'].upper()})",
                f"${coin['price']:,.2f}",
                f"{price_change:.2f}%" if price_change else None,
                delta_color=delta_color
            )
    
    # ----- PRICE COMPARISON CHART -----
    st.header("Price Comparison")
    
    # Select coins to display in chart
    selected_coins = st.multiselect(
        "Select coins to display",
        options=[coin["name"] for coin in all_coins],
        default=[all_coins[0]["name"], all_coins[1]["name"]] if len(all_coins) > 1 else [all_coins[0]["name"]]
    )
    
    if selected_coins:
        # Create interactive chart
        fig = go.Figure()
        
        for coin_name in selected_coins:
            history = get_price_history(coin_name)
            
            if history:
                # Convert to DataFrame and prepare data
                history_df = pd.DataFrame(history)
                history_df["timestamp"] = pd.to_datetime(history_df["timestamp"])
                history_df = history_df.sort_values("timestamp")
                
                # Add line to chart
                fig.add_trace(go.Scatter(
                    x=history_df["timestamp"],
                    y=history_df["price"],
                    mode="lines",
                    name=coin_name
                ))
        
        # Configure chart layout
        fig.update_layout(
            title="Price History",
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            legend_title="Coins",
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ----- USER'S TRACKED COINS SECTION -----
    if "token" in st.session_state:
        st.header("Your Tracked Coins")
        
        user_coins = get_user_coins()
        all_coins_dict = {coin["name"]: coin for coin in all_coins}
        
        if user_coins:
            # Display user's tracked coins
            for coin in user_coins:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    coin_data = all_coins_dict.get(coin["name"], {})
                    price = coin_data.get("price", "N/A")
                    change = coin_data.get("change_24h", "N/A")
                    
                    st.write(f"### {coin['name']} ({coin['symbol'].upper()})")
                    st.write(f"**Price:** ${price:,.2f}" if isinstance(price, (int, float)) else f"**Price:** {price}")
                    st.write(f"**24h Change:** {change:.2f}%" if isinstance(change, (int, float)) else f"**24h Change:** {change}")
                
                with col2:
                    if st.button(f"Remove {coin['symbol'].upper()}", key=f"remove_{coin['id']}"):
                        if remove_coin_from_tracking(coin["id"]):
                            st.rerun()
                
                st.markdown("---")
        else:
            st.info("You are not tracking any coins yet.")
        
        # ----- ADD COINS SECTION -----
        st.header("Add Coins to Track")
        
        # Simplified approach - just show all coins with Add buttons
        for coin in all_coins:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"### {coin['name']} ({coin['symbol'].upper()})")
                st.write(f"**Price:** ${coin['price']:,.2f}")
            
            with col2:
                # Create a unique key for each button
                button_key = f"add_{coin['name']}_{coin['symbol']}"
                if st.button(f"Add {coin['symbol'].upper()}", key=button_key):
                    # Try to add the coin using its database ID if available
                    coin_id = coin.get("id", 1)  # Default to 1 if no ID
                    if add_coin_to_tracking(coin_id):
                        st.rerun()
            
            st.markdown("---")
        else:
            st.info("You are already tracking all available coins.")
    
    # ----- MARKET OVERVIEW SECTION -----
    st.header("Market Overview")
    
    # Create a table with detailed market data
    market_data = []
    for coin in all_coins:
        market_data.append({
            "Name": coin["name"],
            "Symbol": coin["symbol"].upper(),
            "Price (USD)": f"${coin['price']:,.2f}",
            "24h Change": f"{coin.get('change_24h', 'N/A'):.2f}%" if coin.get('change_24h') is not None else "N/A",
            "24h Volume": f"${coin.get('volume_24h', 'N/A'):,.0f}" if coin.get('volume_24h') is not None else "N/A",
            "Market Cap": f"${coin.get('market_cap', 'N/A'):,.0f}" if coin.get('market_cap') is not None else "N/A"
        })
    
    market_df = pd.DataFrame(market_data)
    st.dataframe(market_df, use_container_width=True)

# ----- MAIN APPLICATION ENTRY POINT -----

def main():
    """Main application entry point"""
    # Initialize session state for page navigation
    if "page" not in st.session_state:
        st.session_state["page"] = "login"
    
    # Show appropriate page based on authentication state
    if "token" in st.session_state:
        show_dashboard()
    elif st.session_state["page"] == "register":
        register()
    else:
        login()

# Application entry point
if __name__ == "__main__":
    main()