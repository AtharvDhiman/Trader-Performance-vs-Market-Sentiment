import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Trader Performance Dashboard",
    page_icon="📈",
    layout="wide"
)

# -----------------------------
# Header
# -----------------------------
st.title("📈 Trader Performance vs Market Sentiment")

st.markdown("""
### Data Science Internship Assessment

This dashboard analyzes the relationship between Bitcoin Market Sentiment (Fear & Greed Index)
and Hyperliquid Trader Performance.
""")

st.divider()




import pandas as pd

# Load datasets
historical_df = pd.read_csv("data/historical_data.csv")
fear_greed_df = pd.read_csv("data/fear_greed_index.csv")




st.subheader("📂 Dataset Information")

col1, col2 = st.columns(2)

with col1:
    st.metric("Historical Records", len(historical_df))

with col2:
    st.metric("Fear & Greed Records", len(fear_greed_df))




    # ============================
# Data Preparation
# ============================

# Convert Historical Timestamp
historical_df["Timestamp IST"] = pd.to_datetime(
    historical_df["Timestamp IST"],
    dayfirst=True,
    errors="coerce"
)

# Create Trade Date
historical_df["Trade_Date"] = historical_df["Timestamp IST"].dt.date

# Convert Fear & Greed Date
fear_greed_df["date"] = pd.to_datetime(
    fear_greed_df["date"],
    errors="coerce"
)

fear_greed_df["Trade_Date"] = fear_greed_df["date"].dt.date

# Rename column
fear_greed_df.rename(
    columns={
        "classification":"Market Sentiment"
    },
    inplace=True
)

# Merge datasets
merged_df = historical_df.merge(
    fear_greed_df[
        ["Trade_Date","Market Sentiment"]
    ],
    on="Trade_Date",
    how="left"
)

# Profit / Loss Flag
merged_df["Trade Result"] = merged_df["Closed PnL"].apply(
    lambda x: "Profit" if x > 0 else "Loss"
)



# ============================
# Sidebar
# ============================

st.sidebar.title("⚙ Dashboard Filters")

# Sentiment Filter
sentiment = st.sidebar.multiselect(
    "Market Sentiment",
    merged_df["Market Sentiment"].dropna().unique(),
    default=merged_df["Market Sentiment"].dropna().unique()
)

# Side Filter
trade_side = st.sidebar.multiselect(
    "Trade Side",
    merged_df["Side"].unique(),
    default=merged_df["Side"].unique()
)

# Coin Filter
coin = st.sidebar.multiselect(
    "Coin",
    merged_df["Coin"].unique(),
    default=merged_df["Coin"].unique()
)

# Filter Dataset
filtered_df = merged_df[
    (merged_df["Market Sentiment"].isin(sentiment)) &
    (merged_df["Side"].isin(trade_side)) &
    (merged_df["Coin"].isin(coin))
]



# ============================
# KPI Cards
# ============================

st.header("📊 Key Performance Indicators")

col1,col2,col3,col4,col5 = st.columns(5)

with col1:
    st.metric(
        "Total Trades",
        f"{len(filtered_df):,}"
    )

with col2:
    st.metric(
        "Total PnL",
        f"${filtered_df['Closed PnL'].sum():,.2f}"
    )

with col3:
    st.metric(
        "Average Trade",
        f"${filtered_df['Size USD'].mean():,.2f}"
    )

with col4:
    st.metric(
        "Average Fee",
        f"${filtered_df['Fee'].mean():,.2f}"
    )

with col5:
    win_rate = (
        (filtered_df["Closed PnL"] > 0).mean()*100
    )

    st.metric(
        "Win Rate",
        f"{win_rate:.2f}%"
    )


# ============================
# Average PnL by Market Sentiment
# ============================

st.markdown("---")
st.header("📊 Market Sentiment Analysis")

pnl_sentiment = (
    filtered_df.groupby("Market Sentiment")["Closed PnL"]
    .mean()
    .reset_index()
)

fig1 = px.bar(
    pnl_sentiment,
    x="Market Sentiment",
    y="Closed PnL",
    color="Market Sentiment",
    title="Average Closed PnL by Market Sentiment"
)

st.plotly_chart(fig1, use_container_width=True)



# 2. Profit vs Loss Distribution

trade_result = (
    filtered_df["Trade Result"]
    .value_counts()
    .reset_index()
)

trade_result.columns = ["Trade Result", "Count"]

fig2 = px.pie(
    trade_result,
    names="Trade Result",
    values="Count",
    title="Profit vs Loss Distribution"
)

st.plotly_chart(fig2, use_container_width=True)



# Buy vs Sell Analysis

buy_sell = (
    filtered_df["Side"]
    .value_counts()
    .reset_index()
)

buy_sell.columns = ["Side", "Trades"]

fig3 = px.bar(
    buy_sell,
    x="Side",
    y="Trades",
    color="Side",
    title="Buy vs Sell Trades"
)

st.plotly_chart(fig3, use_container_width=True)



# Top 10 Traded Coins

top_coin = (
    filtered_df["Coin"]
    .value_counts()
    .head(10)
    .reset_index()
)

top_coin.columns = ["Coin", "Trades"]

fig4 = px.bar(
    top_coin,
    x="Coin",
    y="Trades",
    color="Trades",
    title="Top 10 Most Traded Coins"
)

st.plotly_chart(fig4, use_container_width=True)


# Daily Trading Activity
daily_trade = (
    filtered_df.groupby("Trade_Date")
    .size()
    .reset_index(name="Trades")
)

fig5 = px.line(
    daily_trade,
    x="Trade_Date",
    y="Trades",
    title="Daily Trading Activity"
)

st.plotly_chart(fig5, use_container_width=True)

# Average Trade Size by Coin

trade_size = (
    filtered_df.groupby("Coin")["Size USD"]
    .mean()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

fig6 = px.bar(
    trade_size,
    x="Coin",
    y="Size USD",
    color="Size USD",
    title="Average Trade Size by Coin"
)

st.plotly_chart(fig6, use_container_width=True)


# Interactive Data Table

st.markdown("---")
st.header("📄 Filtered Dataset")

st.dataframe(filtered_df)


# Download Button

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="📥 Download Filtered Dataset",
    data=csv,
    file_name="filtered_trader_data.csv",
    mime="text/csv"
)

# Footer

st.markdown("---")

st.caption(
    "Developed by Atharv Dhiman | Data Science Internship Assessment | Primetrade.ai"
)

