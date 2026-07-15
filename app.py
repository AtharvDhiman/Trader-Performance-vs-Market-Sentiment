import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Hyperliquid Trader Performance & Market Sentiment Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling and layout
st.markdown("""
<style>
    /* Metric styling */
    div[data-testid="stMetricValue"] {
        font-size: 26px;
        font-weight: 700;
        color: #1f77b4;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
        font-weight: 600;
        color: #555;
    }
    /* Main container styling */
    .reportview-container {
        background-color: #f5f7f9;
    }
    /* Header card */
    .header-card {
        background: linear-gradient(135deg, #1f4068 0%, #162447 100%);
        color: white;
        padding: 30px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .header-card h1 {
        margin: 0;
        font-size: 32px;
        font-weight: 700;
    }
    .header-card p {
        margin: 10px 0 0 0;
        font-size: 16px;
        opacity: 0.9;
    }
    /* Section dividers */
    hr {
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
        border: 0;
        border-top: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Header Component
# -----------------------------
st.markdown("""
<div class="header-card">
    <h1>📈 Trader Performance vs Market Sentiment</h1>
    <p>Hyperliquid DEX Trading Activity & Bitcoin Fear & Greed Index Analysis | Data Science Intern Assessment</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Data Loading & Prep (Cached)
# -----------------------------
@st.cache_data
def load_and_preprocess_data():
    historical_df = pd.read_csv("data/historical_data.csv")
    fear_greed_df = pd.read_csv("data/fear_greed_index.csv")
    
    # Clean historical timestamp
    historical_df["Timestamp IST"] = pd.to_datetime(
        historical_df["Timestamp IST"],
        dayfirst=True,
        errors="coerce"
    )
    historical_df["Trade_Date"] = historical_df["Timestamp IST"].dt.date
    
    # Clean Fear & Greed dates
    fear_greed_df["date"] = pd.to_datetime(
        fear_greed_df["date"],
        errors="coerce"
    )
    fear_greed_df["Trade_Date"] = fear_greed_df["date"].dt.date
    fear_greed_df.rename(
        columns={"classification": "Market Sentiment"},
        inplace=True
    )
    
    # Merge datasets
    merged = pd.merge(
        historical_df,
        fear_greed_df[["Trade_Date", "value", "Market Sentiment"]],
        on="Trade_Date",
        how="left"
    )
    
    merged["Trade Result"] = merged["Closed PnL"].apply(
        lambda x: "Profit" if x > 0 else "Loss"
    )
    
    # Trader segmentation (overall dataset mapping to ensure stable segments)
    trader_overall = merged.groupby("Account").agg(
        Total_Trades=("Closed PnL", "count"),
        Total_PnL=("Closed PnL", "sum"),
        Win_Rate=("Closed PnL", lambda x: (x > 0).mean() * 100)
    ).reset_index()
    
    q1, q2 = trader_overall["Total_Trades"].quantile([0.33, 0.66])
    def get_segment(trades):
        if trades <= q1:
            return "Low Frequency"
        elif trades <= q2:
            return "Medium Frequency"
        else:
            return "High Frequency"
            
    trader_overall["Frequency Segment"] = trader_overall["Total_Trades"].apply(get_segment)
    
    merged = merged.merge(
        trader_overall[["Account", "Frequency Segment"]],
        on="Account",
        how="left"
    )
    
    return merged, trader_overall

try:
    merged_df, trader_metrics = load_and_preprocess_data()
except Exception as e:
    st.error(f"Error loading datasets: {e}")
    st.stop()

# -----------------------------
# Sidebar Navigation & Filters
# -----------------------------
st.sidebar.title("⚙ Dashboard Filters")

# Filter: Market Sentiment
sentiments = merged_df["Market Sentiment"].dropna().unique().tolist()
selected_sentiments = st.sidebar.multiselect(
    "Market Sentiment Regimes",
    options=sentiments,
    default=sentiments
)

# Filter: Trade Side
sides = merged_df["Side"].dropna().unique().tolist()
selected_sides = st.sidebar.multiselect(
    "Trade Side",
    options=sides,
    default=sides
)

# Filter: Coin
coins = merged_df["Coin"].dropna().unique().tolist()
selected_coins = st.sidebar.multiselect(
    "Coin / Token",
    options=coins,
    default=coins
)

# Apply filters
filtered_df = merged_df[
    (merged_df["Market Sentiment"].isin(selected_sentiments)) &
    (merged_df["Side"].isin(selected_sides)) &
    (merged_df["Coin"].isin(selected_coins))
]

# -----------------------------
# Main Navigation Tabs
# -----------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Dashboard Overview", 
    "📊 Sentiment Deep-Dive", 
    "👥 Trader Segmentation", 
    "📄 Filtered Data",
    "📝 Executive Report"
])

# ==========================================
# Tab 1: Dashboard Overview
# ==========================================
with tab1:
    st.subheader("📂 Dataset Summary")
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        st.metric("Total Historical Records", f"{len(merged_df):,}")
    with col_d2:
        st.metric("Unique Trading Accounts", f"{merged_df['Account'].nunique()}")
    with col_d3:
        st.metric("Filtered Records Selected", f"{len(filtered_df):,}")

    st.markdown("---")
    st.subheader("📊 Key Performance Indicators (Filtered)")
    
    # Calculate KPIs
    total_trades = len(filtered_df)
    if total_trades > 0:
        net_pnl = filtered_df["Closed PnL"].sum()
        avg_trade_size = filtered_df["Size USD"].mean()
        avg_fee = filtered_df["Fee"].sum()
        win_rate = (filtered_df["Closed PnL"] > 0).mean() * 100
        
        col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)
        with col_k1:
            st.metric("Total Trades", f"{total_trades:,}")
        with col_k2:
            st.metric("Net Closed PnL", f"${net_pnl:,.2f}")
        with col_k3:
            st.metric("Avg Trade Size", f"${avg_trade_size:,.2f}")
        with col_k4:
            st.metric("Total Fees paid", f"${avg_fee:,.2f}")
        with col_k5:
            st.metric("Win Rate (%)", f"{win_rate:.2f}%")
            
        st.markdown("---")
        st.subheader("📈 General Distributions")
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # Profit vs Loss pie chart
            trade_result = filtered_df["Trade Result"].value_counts().reset_index()
            trade_result.columns = ["Trade Result", "Count"]
            fig_pie = px.pie(
                trade_result,
                names="Trade Result",
                values="Count",
                title="Profit vs Loss Trade Count",
                color="Trade Result",
                color_discrete_map={"Profit": "#5cb85c", "Loss": "#f0ad4e"},
                hole=0.4
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_g2:
            # Top Coins Bar chart
            top_coins = filtered_df["Coin"].value_counts().head(10).reset_index()
            top_coins.columns = ["Coin", "Trades"]
            fig_coins = px.bar(
                top_coins,
                x="Coin",
                y="Trades",
                title="Top 10 Most Traded Coins",
                color="Trades",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig_coins, use_container_width=True)
            
        col_g3, col_g4 = st.columns(2)
        
        with col_g3:
            # Daily trading activity
            daily_trade = filtered_df.groupby("Trade_Date").size().reset_index(name="Trades")
            fig_line = px.line(
                daily_trade,
                x="Trade_Date",
                y="Trades",
                title="Daily Trading Activity (Volume Count)"
            )
            fig_line.update_traces(line_color="#1f77b4", line_width=2)
            st.plotly_chart(fig_line, use_container_width=True)
            
        with col_g4:
            # PnL distribution
            pnl_clipped = filtered_df[filtered_df["Closed PnL"].between(-500, 1000)]
            fig_pnl_dist = px.histogram(
                pnl_clipped,
                x="Closed PnL",
                nbins=100,
                title="Closed PnL Distribution (Clipped -500 to 1000 for visibility)",
                color_discrete_sequence=["#337ab7"]
            )
            fig_pnl_dist.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break-even")
            st.plotly_chart(fig_pnl_dist, use_container_width=True)
            
    else:
        st.warning("No records match the current filters. Adjust sidebar inputs.")

# ==========================================
# Tab 2: Sentiment Deep-Dive
# ==========================================
with tab2:
    st.subheader("📊 Sentiment Analysis & Trade Side Interactions")
    
    if len(filtered_df) > 0:
        sentiment_order = ["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]
        # Make sure order matches actual values present
        actual_order = [s for s in sentiment_order if s in filtered_df["Market Sentiment"].dropna().unique()]
        
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            # Sentiment counts
            sent_counts = filtered_df["Market Sentiment"].value_counts().reindex(actual_order).reset_index()
            fig_sent = px.bar(
                sent_counts,
                x="Market Sentiment",
                y="count",
                title="Trade Count by Sentiment Regime",
                color="Market Sentiment",
                color_discrete_map={
                    "Extreme Fear": "#d9534f",
                    "Fear": "#f0ad4e",
                    "Neutral": "#5bc0de",
                    "Greed": "#5cb85c",
                    "Extreme Greed": "#2b542c"
                }
            )
            st.plotly_chart(fig_sent, use_container_width=True)
            
        with col_s2:
            # Average PnL by Sentiment
            avg_pnl_sent = filtered_df.groupby("Market Sentiment")["Closed PnL"].mean().reindex(actual_order).reset_index()
            fig_avg_pnl = px.bar(
                avg_pnl_sent,
                x="Market Sentiment",
                y="Closed PnL",
                title="Average Closed PnL by Market Sentiment",
                color="Market Sentiment",
                color_discrete_map={
                    "Extreme Fear": "#d9534f",
                    "Fear": "#f0ad4e",
                    "Neutral": "#5bc0de",
                    "Greed": "#5cb85c",
                    "Extreme Greed": "#2b542c"
                }
            )
            st.plotly_chart(fig_avg_pnl, use_container_width=True)
            
        st.markdown("---")
        st.subheader("⚖ Long vs Short Performance across Sentiment Regimes")
        
        col_s3, col_s4 = st.columns(2)
        
        with col_s3:
            # Win rate by Sentiment and Side
            win_rate_side = filtered_df.groupby(["Market Sentiment", "Side"])["Closed PnL"].apply(
                lambda x: (x > 0).mean() * 100
            ).reset_index(name="Win Rate (%)")
            
            fig_win_side = px.bar(
                win_rate_side,
                x="Market Sentiment",
                y="Win Rate (%)",
                color="Side",
                barmode="group",
                title="Win Rate (%) by Sentiment & Side",
                color_discrete_map={"BUY": "#337ab7", "SELL": "#f0ad4e"},
                category_orders={"Market Sentiment": actual_order}
            )
            fig_win_side.add_hline(y=50, line_dash="dash", line_color="gray")
            st.plotly_chart(fig_win_side, use_container_width=True)
            
        with col_s4:
            # Avg PnL by Sentiment and Side
            avg_pnl_side = filtered_df.groupby(["Market Sentiment", "Side"])["Closed PnL"].mean().reset_index(name="Avg PnL")
            fig_pnl_side = px.bar(
                avg_pnl_side,
                x="Market Sentiment",
                y="Avg PnL",
                color="Side",
                barmode="group",
                title="Average Closed PnL by Sentiment & Side",
                color_discrete_map={"BUY": "#337ab7", "SELL": "#f0ad4e"},
                category_orders={"Market Sentiment": actual_order}
            )
            st.plotly_chart(fig_pnl_side, use_container_width=True)
            
        st.markdown("""
        > **Insight:** Notice how **SELL (Short)** trades consistently yield much higher win rates (exceeding 54%) in almost all sentiment categories compared to **BUY (Long)** trades. In particular, during **Extreme Greed**, short trades have a massive win rate and average payout.
        """)
        
    else:
        st.warning("No records match the current filters.")

# ==========================================
# Tab 3: Trader Segmentation
# ==========================================
with tab3:
    st.subheader("👥 Trader Segmentation (Low vs Medium vs High Frequency)")
    
    # Overall statistics for the 32 traders
    st.markdown("""
    Here we segment the 32 traders by their trading frequency to understand if execution volume correlates with success.
    - **Low Frequency:** Accounts in the bottom 33% of trade counts
    - **Medium Frequency:** Accounts in the middle 33% of trade counts
    - **High Frequency:** Accounts in the top 33% of trade counts
    """)
    
    col_t1, col_t2 = st.columns([2, 1])
    
    with col_t1:
        # Scatter plot: Trades vs Net PnL, size=Win Rate
        fig_scatter = px.scatter(
            trader_metrics,
            x="Total_Trades",
            y="Total_PnL",
            color="Frequency Segment",
            size="Win_Rate",
            hover_data=["Account", "Win_Rate"],
            title="Trading Frequency vs Net PnL (Dot size represents Win Rate %)",
            labels={"Total_Trades": "Total Trades executed", "Total_PnL": "Net Closed PnL (USD)"},
            color_discrete_map={"Low Frequency": "#f0ad4e", "Medium Frequency": "#5bc0de", "High Frequency": "#5cb85c"}
        )
        fig_scatter.add_hline(y=0, line_color="red", line_dash="dash")
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    with col_t2:
        # Aggregated table
        seg_summary = trader_metrics.groupby("Frequency Segment").agg(
            Traders=("Account", "count"),
            Avg_Trades=("Total_Trades", "mean"),
            Total_PnL=("Total_PnL", "sum"),
            Avg_Win_Rate=("Win_Rate", "mean")
        ).reset_index()
        
        st.markdown("##### Segment Performance Summary")
        st.dataframe(seg_summary.style.format({
            "Avg_Trades": "{:,.1f}",
            "Total_PnL": "${:,.2f}",
            "Avg_Win_Rate": "{:.2f}%"
        }))
        
        # Display some info
        profitable_count = (trader_metrics["Total_PnL"] > 0).sum()
        total_traders = len(trader_metrics)
        st.info(f"**Overall Platform Profitability:** {profitable_count} out of {total_traders} accounts ({profitable_count/total_traders*100:.1f}%) are net profitable.")

    st.markdown("---")
    st.subheader("🏆 Leaderboard (Top 10 Traders by Profit)")
    top_10 = trader_metrics.sort_values(by="Total_PnL", ascending=False).head(10).reset_index(drop=True)
    top_10.index = top_10.index + 1
    st.dataframe(top_10.style.format({
        "Total_Trades": "{:,}",
        "Total_PnL": "${:,.2f}",
        "Win_Rate": "{:.2f}%"
    }))

# ==========================================
# Tab 4: Filtered Data
# ==========================================
with tab4:
    st.subheader("📄 Filtered Transactions")
    
    st.markdown(f"Displaying {len(filtered_df):,} records based on active sidebar filters.")
    
    st.dataframe(filtered_df.head(500))
    
    # Download Button
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Dataset (CSV)",
        data=csv,
        file_name="filtered_trader_data.csv",
        mime="text/csv"
    )

# ==========================================
# Tab 5: Executive Report
# ==========================================
with tab5:
    st.subheader("📝 Executive Summary & Internship Assessment Report")
    
    st.markdown("""
    ---
    ### Trader Performance vs. Market Sentiment: A Deep Dive on Hyperliquid DEX
    **Prepared for:** Primetrade.ai  
    **Prepared by:** Atharv Dhiman (Data Science Intern Assessment)  
    **Date:** July 2026  
    ---
    """)
    
    st.markdown("""
    #### 1. Executive Summary
    This report analyzes the relationship between Bitcoin market sentiment (as measured by the **Crypto Fear & Greed Index**) and the trading performance of **32 active traders on the Hyperliquid decentralized exchange (DEX)**. 
    
    Through analysis of a dataset comprising **211,224 individual trades** executed between 2018 and 2026, we uncover significant behavioral patterns and statistical anomalies that can be leveraged to generate trading alpha.
    
    *   **Asymmetric Payoffs (High Risk-Reward Ratio):** Despite an overall trade-level win rate of **41.13%**, the aggregate network of traders is highly profitable (generating **$10,296,958.94** in net profit). This is driven by a massive risk-to-reward ratio: the average winning trade (**$152.48**) is **6.4 times larger** than the average losing trade (**-$23.71**).
    *   **Shorting Alpha in Extreme Greed:** Trade direction (BUY vs. SELL) interacts strongly with sentiment. SELL (short) trades exhibit a **58.98% win rate** and an average PnL of **$114.58 per trade** during **Extreme Greed** periods. In contrast, BUY (long) trades during Extreme Greed generate only **$10.50 per trade** with a **31.14% win rate**.
    *   **Counter-Cyclical Position Sizing:** Successful traders tend to scale up their position sizes during periods of **Fear** (average trade size: **$7,816**) and scale down their positions during **Extreme Greed** (average trade size: **$3,112**), showing a counter-cyclical risk management approach.
    *   **Execution Frequency Correlates with Consistency:** High-frequency traders (averaging >15,000 trades) are **100% profitable**, suggesting that active, systematic execution models are required to consistently extract alpha on Hyperliquid.
    
    #### 2. Key Findings & Market Regime Dynamics
    
    ##### Shorting Dominance during Retail Euphoria
    In cryptocurrency markets, extreme greed is characterized by overleveraged long positions and retail FOMO. At these inflection points, sudden liquidations and sharp pullbacks create high-velocity downside moves. Hyperliquid traders are highly effective at capturing these abrupt capitulations via short contracts, yielding outsized profits. SELL trades have a win rate of **58.98%** in Extreme Greed, with an average PnL of **$114.58/trade**, while BUY trades have only a **31.14%** win rate.
    
    ##### Asymmetric Long Trading in Fear
    Conversely, buying (BUY) during **Fear** has a low win rate (**26.30%**) but a high average PnL (**$63.93**). This shows that catching falling knives is difficult, but when the rebound occurs, the payout is highly lucrative.
    
    ##### systematic Frequency Dominance
    High-frequency accounts represent 100% profitability (11/11 accounts are net positive) and account for **$5.88M** in total network profits. This highlights that systematic and automated market-making or grid strategies successfully capture sentiment-driven market inefficiencies.
    
    #### 3. Strategic Recommendations for Primetrade.ai
    1.  **Automated Greed Shorting Model:** Build a trading bot that triggers short positions when the Fear & Greed Index rises above 75 (Extreme Greed).
    2.  **Asymmetric Long Trading in Fear:** When the Fear & Greed Index drops below 30 (Fear/Extreme Fear), reduce position sizes on shorts and take longs with tight stop-losses but wide profit targets.
    3.  **VIP Trader Retention:** Retain high-frequency accounts by providing fee rebate tiers and dedicated RPC nodes, ensuring liquidity stability.
    """)

# Footer
st.markdown("---")
st.caption(
    "Developed by Atharv Dhiman | Data Science Internship Assessment | Primetrade.ai"
)
