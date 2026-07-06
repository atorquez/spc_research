import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Modern Alpaca SDK Imports
from alpaca.data.historical import CryptoHistoricalDataClient # standard data client
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.live import StockDataStream
from alpaca.trading.client import TradingClient

# ==============================================================================
# 1. CONFIGURATION & API KEYS
# ==============================================================================
API_KEY = "YOUR_ALPACA_API_KEY"
SECRET_KEY = "YOUR_ALPACA_SECRET_KEY"
SYMBOL = "TQQQ"

# Toggle this to True if you want the script to automatically execute trades
LIVE_TRADING_ENABLED = False 

# ==============================================================================
# 2. TRAIN THE INITIAL AI MODEL
# ==============================================================================
# For production, you would load a pre-trained model file here. 
# For this example, we generate dummy historical patterns to initialize the architecture.
def train_mock_model():
    np.random.seed(42)
    mock_data = pd.DataFrame({'Close': 50 + np.cumsum(np.random.normal(0, 0.5, 1000))})
    mock_data['EMA_9'] = mock_data['Close'].ewm(span=9, adjust=False).mean()
    mock_data['EMA_20'] = mock_data['Close'].ewm(span=20, adjust=False).mean()
    mock_data['EMA_Spread'] = mock_data['EMA_9'] - mock_data['EMA_20']
    mock_data['Spread_Change'] = mock_data['EMA_Spread'].diff()
    mock_data.dropna(inplace=True)
    
    X = mock_data[['EMA_Spread', 'Spread_Change']]
    y = np.where(mock_data['Close'].shift(-1) > mock_data['Close'], 1, 0)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

print("Training initial machine learning model...")
ai_model = train_mock_model()

# Create a rolling memory buffer to calculate accurate real-time EMAs
price_history = []

# Initialize Alpaca Trading Client (for paper trading execution)
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# ==============================================================================
# 3. LIVE STREAMING DATA AND PREDICTION ENGINE
# ==============================================================================
async def handle_minute_bar(bar):
    """
    This function triggers automatically every single minute 
    the exact moment a new 1-minute candle closes.
    """
    global price_history
    
    # Extract the close price from the live Alpaca bar object
    current_close = bar.close
    price_history.append(current_close)
    
    # Keep our calculation memory efficient (only need enough to calculate EMA 20)
    if len(price_history) > 100:
        price_history.pop(0)
        
    # We need at least 20 minutes of live data to accurately calculate the EMAs
    if len(price_history) < 20:
        print(f"Collecting data... {len(price_history)}/20 minutes stored.")
        return

    # Convert rolling memory to a Pandas Series to use calculation features
    series = pd.Series(price_history)
    ema_9 = series.ewm(span=9, adjust=False).mean().iloc[-1]
    ema_20 = series.ewm(span=20, adjust=False).mean().iloc[-1]
    
    # Calculate current spread
    current_spread = ema_9 - ema_20
    
    # Calculate previous spread to determine the 'Spread_Change' velocity feature
    prev_ema_9 = series.iloc[:-1].ewm(span=9, adjust=False).mean().iloc[-1]
    prev_ema_20 = series.iloc[:-1].ewm(span=20, adjust=False).mean().iloc[-1]
    prev_spread = prev_ema_9 - prev_ema_20
    spread_change = current_spread - prev_spread
    
    # Format the exact feature matrix the AI model expects
    features = np.array([[current_spread, spread_change]])
    
    # Generate live model prediction (1 = Price will rise next minute, 0 = Will fall/flat)
    prediction = ai_model.predict(features)[0]
    
    print(f"Time: {bar.timestamp} | Close: ${current_close:.2f} | EMA Spread: {current_spread:.4f}")
    
    # ==============================================================================
    # 4. TRADE EXECUTION LOGIC (TQQQ vs SQQQ)
    # ==============================================================================
    if prediction == 1:
        print("➔ AI Signal: BULLISH. Action: Buy TQQQ / Sell SQQQ")
        if LIVE_TRADING_ENABLED:
            # Code to execute Market Orders via Alpaca API would go here
            pass
    else:
        print("➔ AI Signal: BEARISH. Action: Buy SQQQ / Sell TQQQ")
        if LIVE_TRADING_ENABLED:
            pass

# ==============================================================================
# 5. INITIALIZE THE LIVE WEBSOCKET
# ==============================================================================
# Connect to Alpaca's live raw data stream
stream = StockDataStream(API_KEY, SECRET_KEY)

# Subscribe our custom handler function to the 1-minute bar feed for TQQQ
stream.subscribe_bars(handle_minute_bar, SYMBOL)

print(f"Successfully authenticated with Alpaca. Streaming live 1-min data for {SYMBOL}...")
stream.run()