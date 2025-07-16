# app.py

import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime
import os
from model.ai_model import prepare_features, train_and_predict

# Page config
st.set_page_config(page_title="AutoTrade AI", layout="wide")

# Custom CSS
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
        }
        .stButton>button {
            border-radius: 6px;
        }
        .stDataFrame {
            overflow-x: auto;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📈 AutoTrade AI – Your Personal AI Trading Assistant")

# Stock Selector
nifty_stocks = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'ITC.NS', 'HDFCBANK.NS']
stock = st.selectbox("📌 Choose a stock", nifty_stocks)

# Date Range
st.sidebar.subheader("📅 Select Date Range")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# Fetch Data
@st.cache_data
def get_data(symbol, start, end):
    return yf.download(symbol, start=start, end=end)

data = get_data(stock, start_date, end_date)

# Price Chart
st.subheader(f"💹 Price Chart for {stock}")
if not data.empty:
    st.line_chart(data['Close'])
else:
    st.warning("⚠️ No data available for the selected range.")

# Raw Data
if st.checkbox("Show raw data"):
    st.write(data.tail())

# Technical Indicators
st.subheader("📊 Technical Indicators")
data = data.dropna()

if not data.empty:
    close_series = data['Close'].squeeze()

    # RSI
    data['RSI'] = ta.momentum.RSIIndicator(close_series).rsi()

    # MACD
    macd_indicator = ta.trend.MACD(close_series)
    data['MACD'] = macd_indicator.macd()
    data['MACD_Signal'] = macd_indicator.macd_signal()

    # Flatten any MultiIndex
    data.columns = [col if not isinstance(col, tuple) else col[0] for col in data.columns]

    st.write("**Relative Strength Index (RSI)**")
    st.line_chart(data['RSI'].dropna())

    st.write("**MACD and Signal Line**")
    st.line_chart(data[['MACD', 'MACD_Signal']].dropna())

else:
    st.warning("⚠️ Not enough clean data to show indicators.")

# AI Prediction
st.subheader("🤖 AI Prediction")
prediction = None

if data.empty or len(data) < 30:
    st.warning("⚠️ Not enough data to make a prediction. Try selecting a wider date range.")
else:
    try:
        prediction = train_and_predict(data)
        result_text = "📈 AI Predicts: Price will go UP (BUY)" if prediction == 1 else "📉 AI Predicts: Price will go DOWN (SELL)"
        st.success(result_text)
    except Exception as e:
        st.error(f"⚠️ Could not generate prediction: {e}")
        prediction = -1

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
    prediction_text = "BUY" if prediction == 1 else "SELL"
    entry = f"{now},{stock},{action},{price},{prediction_text}\n"
    with open(log_path, "a") as f:
        f.write(entry)

if trade_action and prediction != -1:
    current_price = round(data['Close'].iloc[-1], 2)
    log_fake_trade(stock, trade_action, current_price, prediction)
    st.success(f"📝 Trade Executed: {trade_action} at ₹{current_price}")

# Show Fake Trade History
st.subheader("📓 Your Fake Trade History")
try:
    fake_log = pd.read_csv("logs/fake_trades.csv")
    st.dataframe(fake_log[::-1], use_container_width=True)
except:
    st.info("No fake trades executed yet.")

# Log AI Prediction
def log_prediction(stock_name, prediction_value):
    os.makedirs("logs", exist_ok=True)
    prediction_text = "BUY" if prediction_value == 1 else "SELL"
    log_path = "logs/trade_log.csv"
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = f"{date_now},{stock_name},{prediction_text}\n"
    with open(log_path, "a") as f:
        f.write(new_entry)

if prediction != -1:
    log_prediction(stock, prediction)

# Show Prediction Log
st.subheader("📜 Trade Log History")
try:
    log_df = pd.read_csv("logs/trade_log.csv")
    st.dataframe(log_df[::-1], use_container_width=True)
except:
    st.warning("⚠️ No trade logs found yet.")

# Trade Performance Summary
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

        for index, row in df.iterrows():
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

            st.metric("Total Profit/Loss", f"₹{round(total_pnl, 2)}")
            st.metric("Win Rate", f"{win_rate}%")
            st.metric("Total Trades", len(trade_df))

            with st.expander("📋 Trade Summary Table"):
                st.dataframe(trade_df)
        else:
            st.info("You haven't completed any BUY-SELL pair yet to calculate profit.")
    except Exception as e:
        st.warning(f"Error calculating performance: {e}")

calculate_profit_loss()
