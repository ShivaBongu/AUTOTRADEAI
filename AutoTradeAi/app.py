import os
from datetime import datetime

import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import streamlit as st
import ta  # Make sure ta is installed (technical analysis lib)

# Page config
st.set_page_config(page_title="AutoTrade AI", layout="wide")

# UI Styling
st.markdown("""
    <style>
        #MainMenu, footer, header {visibility: hidden;}
        .block-container {padding-top: 1rem; padding-bottom: 2rem;}
        .stButton>button {border-radius: 6px;}
        .stDataFrame {overflow-x: auto;}
    </style>
""", unsafe_allow_html=True)

# Title
st.title("📈 AutoTrade AI – Your Personal AI Trading Assistant")

# Sidebar input
st.sidebar.subheader("🗕️ Select Date Range")
default_start = pd.to_datetime("2023-01-01")
default_end = pd.to_datetime("today")
start_date = st.sidebar.date_input("Start Date", default_start)
end_date = st.sidebar.date_input("End Date", default_end)

# Stock selector
nifty_stocks = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'ITC.NS', 'HDFCBANK.NS']
stock = st.selectbox("📌 Choose a stock", nifty_stocks)

# Fetch stock data
@st.cache_data
def get_data(symbol, start, end):
    return yf.download(symbol, start=start, end=end)

data = get_data(stock, start_date, end_date)
st.write("📦 Raw Data Fetched:", data.shape)

# Chart and indicators
if data.empty:
    st.warning("⚠️ No data available to calculate technical indicators.")
else:
    data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
    macd = ta.trend.MACD(data['Close'])
    data['MACD'] = macd.macd()
    data['MACD_Signal'] = macd.macd_signal()

    st.subheader("📊 Relative Strength Index (RSI)")
    st.line_chart(data['RSI'].dropna())

    st.subheader("📉 MACD and Signal Line")
    st.line_chart(data[['MACD', 'MACD_Signal']].dropna())

    st.subheader("🕯️ Candlestick Chart")
    data.index = pd.to_datetime(data.index)
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price'
    )])
    fig.update_layout(title=f"{stock} Price Chart", xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# Placeholder prediction logic
def train_and_predict(data):
    # Dummy: Use RSI + MACD crossover
    if data['MACD'].iloc[-1] > data['MACD_Signal'].iloc[-1] and data['RSI'].iloc[-1] < 70:
        return 1  # Buy
    else:
        return 0  # Sell

# AI Prediction
st.subheader("🤖 AI Prediction")
prediction = -1

if not data.empty and len(data) >= 30:
    try:
        prediction = train_and_predict(data)
        if prediction == 1:
            st.success("📈 AI Predicts: Price will go UP (BUY)")
        else:
            st.info("📉 AI Predicts: Price will go DOWN (SELL)")
    except Exception as e:
        st.error(f"Prediction error: {e}")
else:
    st.warning("⚠️ Not enough data to make a prediction.")

# Simulated Trading
st.subheader("🎮 Simulated Trading")
col1, col2 = st.columns(2)
trade_action = None

if col1.button("✅ Execute BUY Trade"):
    trade_action = "BUY"
elif col2.button("❌ Execute SELL Trade"):
    trade_action = "SELL"

def log_fake_trade(stock, action, price, prediction):
    os.makedirs("logs", exist_ok=True)
    log_path = "logs/fake_trades.csv"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pred_txt = "BUY" if prediction == 1 else "SELL"
    with open(log_path, "a") as f:
        f.write(f"{now},{stock},{action},{price},{pred_txt}\n")

if trade_action and prediction != -1:
    current_price = round(data['Close'].iloc[-1], 2)
    log_fake_trade(stock, trade_action, current_price, prediction)
    st.success(f"📝 Trade Executed: {trade_action} at ₹{current_price}")

# Show Trade History
st.subheader("📓 Your Fake Trade History")
try:
    log = pd.read_csv("logs/fake_trades.csv", names=["Time", "Stock", "Action", "Price", "Prediction"])
    st.dataframe(log[::-1], use_container_width=True)
except:
    st.info("No fake trades executed yet.")

# Prediction Logging
def log_prediction(stock, prediction):
    os.makedirs("logs", exist_ok=True)
    log_path = "logs/trade_log.csv"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pred_txt = "BUY" if prediction == 1 else "SELL"
    with open(log_path, "a") as f:
        f.write(f"{now},{stock},{pred_txt}\n")

if prediction != -1:
    log_prediction(stock, prediction)

st.subheader("📜 Trade Log History")
try:
    log_df = pd.read_csv("logs/trade_log.csv", names=["Time", "Stock", "Prediction"])
    st.dataframe(log_df[::-1], use_container_width=True)
except:
    st.warning("⚠️ No trade logs found yet.")

# Trade Performance
st.subheader("💰 Trade Performance Summary")
def calculate_profit_loss():
    log_path = "logs/fake_trades.csv"
    if not os.path.exists(log_path):
        st.info("No trades to evaluate yet.")
        return

    try:
        df = pd.read_csv(log_path, names=["Time", "Stock", "Action", "Price", "Prediction"])
        df = df[::-1].reset_index(drop=True)

        trades = []
        position = None
        entry_price = 0.0

        for _, row in df.iterrows():
            if row["Action"] == "BUY":
                position = "LONG"
                entry_price = row["Price"]
            elif row["Action"] == "SELL" and position == "LONG":
                pnl = round(row["Price"] - entry_price, 2)
                trades.append({
                    "Entry": entry_price,
                    "Exit": row["Price"],
                    "Profit/Loss": pnl,
                    "Timestamp": row["Time"]
                })
                position = None

        trade_df = pd.DataFrame(trades)
        if not trade_df.empty:
            total_pnl = trade_df["Profit/Loss"].sum()
            wins = trade_df[trade_df["Profit/Loss"] > 0].shape[0]
            losses = trade_df[trade_df["Profit/Loss"] <= 0].shape[0]
            win_rate = round((wins / (wins + losses)) * 100, 2) if wins + losses > 0 else 0

            st.metric("Total Profit/Loss", f"₹{total_pnl}")
            st.metric("Win Rate", f"{win_rate}%")
            st.metric("Total Trades", len(trade_df))

            with st.expander("📋 Trade Summary Table"):
                st.dataframe(trade_df)
        else:
            st.info("You haven't completed any BUY-SELL pair yet.")
    except Exception as e:
        st.warning(f"Error calculating performance: {e}")

calculate_profit_loss()

# Footer
st.markdown("""
    <div style='text-align: center; padding: 10px; font-size: 14px; color: gray;'>
        🚀 Built with ❤️ by <b>Sri Shiva Goud</b> – AutoTrade AI
    </div>
""", unsafe_allow_html=True)
