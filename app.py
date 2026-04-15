import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import yfinance as yf
from dotenv import load_dotenv
import os
from duckduckgo_search import DDGS

# Load environment variables
load_dotenv()

# ---------------- FREE AI FUNCTION ----------------
def simple_stock_ai(symbol, latest_price, change_pct, rsi, news_articles, question):
    response = f"📊 Analysis for {symbol}:\n\n"

    # Price trend
    if change_pct > 0:
        response += "📈 The stock is currently in an upward trend.\n"
    else:
        response += "📉 The stock is currently in a downward trend.\n"

    # RSI analysis
    if rsi > 70:
        response += "⚠️ RSI indicates the stock may be overbought.\n"
    elif rsi < 30:
        response += "💡 RSI indicates the stock may be oversold.\n"
    else:
        response += "✅ RSI is in a neutral range.\n"

    # News
    if news_articles:
        response += f"📰 {len(news_articles)} recent news articles found.\n"

    # Suggestion
    if change_pct > 0 and rsi < 70:
        response += "👍 The stock shows positive momentum.\n"
    else:
        response += "⚠️ Consider analyzing more before investing.\n"

    response += f"\n💬 Your Question: {question}\n"
    response += "👉 This is a basic AI analysis. For real investments, do deeper research."

    return response

# ---------------- STOCK ANALYZER ----------------
class StockAnalyzer:
    def get_stock_data(self, symbol, market):
        try:
            if market == 'Indian Stocks':
                if not (symbol.endswith('.NS') or symbol.endswith('.BO')):
                    ticker = f"{symbol}.NS"
                else:
                    ticker = symbol
            else:
                ticker = symbol.replace('.NS', '').replace('.BO', '')

            stock = yf.Ticker(ticker)
            df = stock.history(period="1y", interval="1wk")

            if df.empty:
                st.error(f"No data found for {ticker}")
                return None

            return df, stock.info

        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            return None, None

    def get_stock_news(self, company_name):
        try:
            with DDGS() as ddgs:
                news_results = ddgs.news(
                    keywords=company_name,
                    region='wt-wt',
                    safesearch='Moderate',
                    timelimit='d',
                    max_results=5
                )
                return list(news_results)
        except Exception as e:
            st.error(f"Error fetching news: {str(e)}")
            return None

    def process_stock_data(self, df):
        if df is None or df.empty:
            return None

        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if all(col in df.columns for col in required_columns):
            return df
        else:
            st.error("Missing required columns")
            return None

    def get_currency_symbol(self, market):
        return '₹' if market == 'Indian Stocks' else '$'

    def format_currency(self, value, symbol):
        return f"{symbol}{value:,.2f}"

# ---------------- MAIN APP ----------------
def main():
    st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")
    st.title("📈 Stock Analysis Dashboard")

    st.sidebar.header("Settings")

    market = st.sidebar.radio("Select Market", ['Indian Stocks', 'US Stocks'])
    symbol = st.sidebar.text_input("Enter Stock Symbol", "RELIANCE.NS")

    analyzer = StockAnalyzer()

    result = analyzer.get_stock_data(symbol, market)
    if result is None:
        return

    df, stock_info = result
    df = analyzer.process_stock_data(df)

    if df is None:
        return

    currency = analyzer.get_currency_symbol(market)

    # Chart
    st.subheader(f"{symbol} Price Chart")
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    )])
    st.plotly_chart(fig, use_container_width=True)

    # Metrics
    latest_price = df['Close'].iloc[-1]
    change = df['Close'].iloc[-1] - df['Close'].iloc[-2]
    change_pct = (change / df['Close'].iloc[-2]) * 100

    st.metric("Price", analyzer.format_currency(latest_price, currency), f"{change_pct:.2f}%")

    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    st.line_chart(df['RSI'])

    # News
    st.subheader("📰 News")
    company_name = stock_info.get('longName', symbol)
    news = analyzer.get_stock_news(company_name)

    if news:
        for n in news:
            st.write(f"[{n['title']}]({n['url']})")

    # Chatbot
    st.subheader("💬 Ask AI")
    question = st.text_input("Ask about this stock")

    if question:
        answer = simple_stock_ai(
            symbol,
            latest_price,
            change_pct,
            df['RSI'].iloc[-1],
            news,
            question
        )
        st.write(answer)

if __name__ == "__main__":
    main()