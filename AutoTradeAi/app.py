import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from ta.trend import MACD
from ta.momentum import RSIIndicator
from datetime import datetime

# Page config
st.set_page_config(page_title="AutoTradeAI", layout="wide")
st.title("🚀 AutoTradeAI - AI Stock Trading Assistant")

# Sidebar setup
st.sidebar.title("Stock Selection & Settings")
default_start = pd.to_datetime("2023-01-01")
default_end = pd.to_datetime("today")

# Tabs for manual vs dropdown
tab1, tab2 = st.tabs(["🔍 Manual Ticker", "📈 Nifty Dropdown"])

with tab1:
    ticker = st.sidebar.text_input("Enter Stock Ticker", "RELIANCE.NS", key="manual_ticker")
    start_date = st.sidebar.date_input("Start Date", default_start, key="start1")
    end_date = st.sidebar.date_input("End Date", default_end, key="end1")

with tab2:
    nifty_stocks = ["RELIANCE.NS", "INFY.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"]
    selected_stock = st.sidebar.selectbox("Select Nifty Stock", nifty_stocks, key="dropdown_ticker")
    start_date_2 = st.sidebar.date_input("Start Date", default_start, key="start2")
    end_date_2 = st.sidebar.date_input("End Date", default_end, key="end2")

# Decide final input
if ticker:
    selected_ticker = ticker
    selected_start = start_date
    selected_end = end_date
else:
    selected_ticker = selected_stock
    selected_start = start_date_2
    selected_end = end_date_2

# Download stock data
try:
    data = yf.download(selected_ticker, start=selected_start, end=selected_end)

    if data.empty:
        st.warning("⚠️ No data found. Please check the ticker or date range.")
    else:
        st.success(f"📊 Data loaded for {selected_ticker}")

        # Add technical indicators
        data["RSI"] = RSIIndicator(data["Close"]).rsi()
        macd = MACD(data["Close"])
        data["MACD"] = macd.macd()
        data["MACD_signal"] = macd.macd_signal()

        # Plotting candlestick
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price'
        ))

        # Plot RSI
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data["RSI"],
            mode='lines',
            name='RSI',
            yaxis='y2',
            line=dict(color='orange')
        ))

        # Plot MACD
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data["MACD"],
            mode='lines',
            name='MACD',
            yaxis='y3',
            line=dict(color='blue')
        ))

        fig.add_trace(go.Scatter(
            x=data.index,
            y=data["MACD_signal"],
            mode='lines',
            name='MACD Signal',
            yaxis='y3',
            line=dict(color='red', dash='dot')
        ))

        # Update layout
        fig.update_layout(
            title=f"{selected_ticker} Candlestick Chart with Indicators",
            xaxis_rangeslider_visible=False,
            yaxis=dict(title='Price'),
            yaxis2=dict(title='RSI', overlaying='y', side='right', showgrid=False),
            yaxis3=dict(title='MACD', anchor="free", overlaying="y", side='right', position=1, showgrid=False),
            template='plotly_dark',
            height=700
        )

        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
