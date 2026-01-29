import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.utils.db import Database
from src.backtest.engine import BacktestEngine
from src.backtest.strategy import MomentumStrategy, SentimentStrategy
from src.backtest.metrics import format_metrics
from src.portfolio.tracker import PortfolioTracker
from src.utils.settings import SettingsManager

# Config
st.set_page_config(page_title="Hedgemony Trading Dashboard", layout="wide")
st.title("🦅 Hedgemony: Event-Driven Alpha Engine")

# DB Connection
@st.cache_resource
def get_db():
    db = Database()
    db.init_db()
    return db

db = get_db()

# Tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Live Trading", "🧪 Backtesting", "📈 Price History", "💼 Portfolio", "⚙️ Settings"])

# ============== TAB 1: LIVE TRADING ==============
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Market Sentiment Tracker")
        news_data = db.get_recent_news(limit=100)
        if news_data:
            df_news = pd.DataFrame(news_data)
            df_news['published_at'] = pd.to_datetime(df_news['published_at'], format='mixed')
            
            fig = px.bar(df_news, x='published_at', y='sentiment_score', 
                         color='sentiment_label', 
                         color_discrete_map={'positive': 'green', 'negative': 'red', 'neutral': 'gray'},
                         title="Sentiment Momentum (Last 100 Events)")
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("⚡️ Latency Tracker")
            # Calculate Latency (Ingested - Published)
            # Note: Published time might be 'just now' so negative latency is good (source was fast)
            # Actually, latency = IngestedAt - PublishedAt
            
            latencies = []
            for n in news_data:
                if n.get('ingested_at') and n.get('published_at'):
                    # Ensure datetime objects
                    ingested = pd.to_datetime(n['ingested_at'], format='mixed')
                    published = pd.to_datetime(n['published_at'], format='mixed')
                    # lag in seconds
                    lag = (ingested - published).total_seconds()
                    latencies.append(lag)
            
            if latencies:
                avg_lag = sum(latencies) / len(latencies)
                st.metric("Avg News Latency", f"{avg_lag:.1f}s", delta_color="inverse")
            else:
                st.info("No latency data yet.")

            st.subheader("Incoming Intelligence")
            st.dataframe(df_news[['published_at', 'title', 'sentiment_score', 'confidence', 'source_id']], 
                         use_container_width=True, hide_index=True)
        else:
            st.info("Waiting for incoming news stream...")
    
    with col2:
        st.subheader("Live Trade Log (Paper)")
        trades_data = db.get_recent_trades(limit=50)
        if trades_data:
            df_trades = pd.DataFrame(trades_data)
            st.dataframe(df_trades[['timestamp', 'side', 'quantity', 'confidence']], use_container_width=True)
            
            total_pnl = df_trades['pnl'].sum()
            total_trades = len(df_trades)
            st.metric("Total Paper PnL", f"${total_pnl:,.2f}")
            st.metric("Total Executions", total_trades)
        else:
            st.info("No trades executed yet.")

# ============== TAB 2: BACKTESTING ==============
with tab2:
    st.subheader("Strategy Backtester")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        symbol = st.selectbox("Symbol", ["BTC-USD", "ETH-USD"])
    with col2:
        strategy_name = st.selectbox("Strategy", ["momentum", "sentiment"])
    with col3:
        start_date = st.date_input("Start Date", datetime(2024, 1, 1))
    with col4:
        end_date = st.date_input("End Date", datetime(2024, 12, 31))
    
    col5, col6 = st.columns(2)
    with col5:
        initial_balance = st.number_input("Initial Balance ($)", value=100000, step=10000)
    with col6:
        position_size = st.slider("Position Size (%)", 1, 20, 5) / 100
    
    if st.button("🚀 Run Backtest", type="primary"):
        with st.spinner("Running backtest..."):
            # Create strategy
            if strategy_name == "momentum":
                strategy = MomentumStrategy()
            else:
                strategy = SentimentStrategy()
            
            # Run backtest
            engine = BacktestEngine(
                strategy=strategy,
                db=db,
                initial_balance=initial_balance,
                position_size_pct=position_size
            )
            
            result = engine.run(
                symbol=symbol,
                start_date=datetime.combine(start_date, datetime.min.time()),
                end_date=datetime.combine(end_date, datetime.min.time())
            )
            
            # Store in session state
            st.session_state['backtest_result'] = result
    
    # Display results if available
    if 'backtest_result' in st.session_state:
        result = st.session_state['backtest_result']
        metrics = result.metrics
        
        st.markdown("---")
        st.subheader("📊 Results")
        
        # KPI Row
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total PnL", f"${metrics.total_pnl:,.2f}", f"{metrics.total_pnl_pct:+.2f}%")
        kpi2.metric("Sharpe Ratio", f"{metrics.sharpe_ratio:.2f}")
        kpi3.metric("Win Rate", f"{metrics.win_rate:.1f}%")
        kpi4.metric("Max Drawdown", f"{metrics.max_drawdown_pct:.2f}%")
        
        kpi5, kpi6, kpi7, kpi8 = st.columns(4)
        kpi5.metric("Total Trades", metrics.total_trades)
        kpi6.metric("Winning", metrics.winning_trades)
        kpi7.metric("Losing", metrics.losing_trades)
        kpi8.metric("Avg Trade", f"${metrics.avg_trade_pnl:,.2f}")
        
        # Equity curve
        if result.trades:
            st.subheader("📈 Equity Curve")
            equity = [result.initial_balance]
            dates = [result.start_date]
            for trade in result.trades:
                equity.append(equity[-1] + trade.pnl)
                dates.append(trade.timestamp)
            
            df_equity = pd.DataFrame({'Date': dates, 'Balance': equity})
            fig = px.line(df_equity, x='Date', y='Balance', title="Portfolio Value Over Time")
            fig.update_traces(line_color='#00d4aa')
            st.plotly_chart(fig, use_container_width=True)
            
            # Trade log
            st.subheader("📋 Trade Log")
            trade_data = [{
                'Date': t.timestamp.strftime('%Y-%m-%d'),
                'Side': t.side.upper(),
                'Entry': f"${t.entry_price:,.0f}",
                'Exit': f"${t.exit_price:,.0f}",
                'PnL': f"${t.pnl:+,.2f}",
                'Reason': t.reason
            } for t in result.trades]
            st.dataframe(pd.DataFrame(trade_data), use_container_width=True, hide_index=True)

# ============== TAB 3: PRICE HISTORY ==============
with tab3:
    st.subheader("Historical Price Data")
    
    col1, col2 = st.columns(2)
    with col1:
        hist_symbol = st.selectbox("Select Symbol", ["BTC-USD", "ETH-USD"], key="hist_symbol")
    with col2:
        limit = st.slider("Days to show", 30, 365, 90)
    
    price_data = db.get_price_history(symbol=hist_symbol, limit=limit)
    
    if price_data:
        df_price = pd.DataFrame(price_data)
        df_price['timestamp'] = pd.to_datetime(df_price['timestamp'])
        
        # Candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=df_price['timestamp'],
            open=df_price['open'],
            high=df_price['high'],
            low=df_price['low'],
            close=df_price['close']
        )])
        fig.update_layout(title=f"{hist_symbol} Price History", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Stats
        st.subheader("📊 Statistics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Current Price", f"${df_price['close'].iloc[-1]:,.2f}")
        col2.metric("Period High", f"${df_price['high'].max():,.2f}")
        col3.metric("Period Low", f"${df_price['low'].min():,.2f}")
        change = ((df_price['close'].iloc[-1] - df_price['close'].iloc[0]) / df_price['close'].iloc[0]) * 100
        col4.metric("Period Change", f"{change:+.2f}%")
    else:
        st.warning("No price data found. Run the backfill script first:")
        st.code("python3 scripts/backfill.py --start 2024-01-01 --end 2024-12-31")

# ============== TAB 4: PORTFOLIO ==============
with tab4:
    st.subheader("Portfolio Performance")
    
    # Initialize tracker
    tracker = PortfolioTracker(db=db)
    stats = tracker.get_current_stats()
    
    # KPI Row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Balance", f"${stats['balance']:,.2f}", f"{stats['total_pnl_pct']:+.2f}%")
    kpi2.metric("Total PnL", f"${stats['total_pnl']:,.2f}")
    kpi3.metric("Win Rate", f"{stats['win_rate']:.1f}%")
    kpi4.metric("Sharpe Ratio", f"{stats['sharpe_ratio']:.2f}")
    
    kpi5, kpi6, kpi7, kpi8 = st.columns(4)
    kpi5.metric("Total Trades", stats['trade_count'])
    kpi6.metric("Max Drawdown", f"{stats['max_drawdown']:.2f}%")
    kpi7.metric("Initial Balance", "$100,000.00")
    
    if st.button("📸 Record Snapshot"):
        snapshot = tracker.record_snapshot()
        st.success(f"Snapshot recorded: ${snapshot.balance:,.2f}")
    
    st.markdown("---")
    
    # Equity curve from trades
    trades_data = db.get_recent_trades(limit=1000)
    if trades_data:
        st.subheader("📈 Equity Curve")
        
        # Build equity curve
        initial_balance = 100000.0
        equity = [initial_balance]
        dates = [datetime.now() - timedelta(days=len(trades_data))]
        
        for i, trade in enumerate(trades_data):
            equity.append(equity[-1] + trade.get('pnl', 0))
            ts = trade.get('timestamp')
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                except:
                    ts = datetime.now()
            dates.append(ts if isinstance(ts, datetime) else datetime.now())
        
        df_equity = pd.DataFrame({'Date': dates, 'Balance': equity})
        fig = px.area(df_equity, x='Date', y='Balance', title="Portfolio Value Over Time")
        fig.update_traces(line_color='#00d4aa', fillcolor='rgba(0, 212, 170, 0.2)')
        st.plotly_chart(fig, use_container_width=True)
        
        # Daily PnL chart
        st.subheader("📊 Trade PnL Distribution")
        pnls = [t.get('pnl', 0) for t in trades_data]
        colors = ['green' if p > 0 else 'red' for p in pnls]
        
        fig = go.Figure(data=[go.Bar(y=pnls, marker_color=colors)])
        fig.update_layout(title="PnL per Trade", xaxis_title="Trade #", yaxis_title="PnL ($)")
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent trades
        st.subheader("📋 Recent Trades")
        df_trades = pd.DataFrame(trades_data[-20:])
        if not df_trades.empty:
            st.dataframe(df_trades[['timestamp', 'symbol', 'side', 'price', 'quantity', 'pnl']], 
                        use_container_width=True, hide_index=True)
    else:
        st.info("No trades recorded yet. Run the engine to generate trades.")

# ============== TAB 5: SETTINGS ==============
with tab5:
    st.subheader("Dynamic Configuration")
    st.info("⚠️ Changes made here are applied immediately to the running bot.")
    
    settings = SettingsManager()
    config = settings.get_all()
    
    # Create form for settings
    with st.form("settings_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🛡️ Risk Management")
            
            # Leverage
            current_leverage = settings.get("trading.risk.max_leverage", 1)
            new_leverage = st.slider("Max Leverage", 1, 125, int(current_leverage), help="Multiplier for position size")
            
            # Position Size
            current_pos_size = settings.get("trading.risk.max_position_size_pct", 0.05)
            new_pos_size = st.slider("Max Position Size (%)", 1, 100, int(current_pos_size * 100)) / 100
            
            # Stop Loss
            current_sl = settings.get("trading.risk.global_stop_loss_pct", 0.02)
            new_sl = st.number_input("Global Stop Loss (%)", 0.1, 50.0, float(current_sl * 100), step=0.1) / 100
            
             # Take Profit
            current_tp = settings.get("trading.risk.take_profit_pct", 0.05)
            new_tp = st.number_input("Take Profit (%)", 0.1, 100.0, float(current_tp * 100), step=0.1) / 100

        with col2:
            st.markdown("### 🧠 Brain / Strategy")
            
            # Confidence Threshold
            current_conf = settings.get("brain.confidence_threshold", 0.85)
            new_conf = st.slider("Confidence Threshold", 0.5, 0.99, float(current_conf), step=0.01, help="Min confidence to trade")
            
            # Impact Multiplier
            st.markdown("#### Advanced")
            st.caption("When news impact is HIGH (8/10+):")
            current_impact_mult = settings.get("brain.use_impact_multiplier", True)
            new_impact_mult = st.checkbox("Double Position Size?", value=current_impact_mult)
            
        submitted = st.form_submit_button("💾 Save Configuration")
        
        if submitted:
            # Save all settings
            settings.set("trading.risk.max_leverage", new_leverage)
            settings.set("trading.risk.max_position_size_pct", new_pos_size)
            settings.set("trading.risk.global_stop_loss_pct", new_sl)
            settings.set("trading.risk.take_profit_pct", new_tp)
            settings.set("brain.confidence_threshold", new_conf)
            settings.set("brain.use_impact_multiplier", new_impact_mult)
            
            st.success("Configuration updated successfully! 🚀")

# Footer
st.markdown("---")
st.caption("Hedgemony Fund Engine v0.3 | Running on Localhost")

