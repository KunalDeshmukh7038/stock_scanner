import os
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from streamlit_autorefresh import st_autorefresh
    AUTO_REFRESH = True
except ImportError:
    AUTO_REFRESH = False

# ── Page Config ──
IS_EMBEDDED = os.environ.get('STREAMLIT_EMBEDDED_DASHBOARD') == '1'

if not IS_EMBEDDED:
    st.set_page_config(
        page_title='MarketPulse India',
        page_icon='📈',
        layout='wide',
        initial_sidebar_state='collapsed'
    )

# ── CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background: #080c14;
    color: #c9d1d9;
}
.main .block-container {
    padding: 1.2rem 1.8rem 2rem;
    max-width: 1600px;
}

/* ── Ticker Bar ── */
.ticker-bar {
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}
.ticker-card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 12px 18px;
    flex: 1;
    min-width: 160px;
    position: relative;
    overflow: hidden;
}
.ticker-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.ticker-card.pos::before { background: #22c55e; }
.ticker-card.neg::before { background: #ef4444; }
.ticker-name {
    font-size: 11px;
    color: #6e7681;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 6px;
}
.ticker-price {
    font-size: 20px;
    font-weight: 600;
    color: #e6edf3;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -0.5px;
}
.ticker-change-pos {
    font-size: 12px;
    color: #22c55e;
    font-family: 'JetBrains Mono', monospace;
    margin-top: 4px;
}
.ticker-change-neg {
    font-size: 12px;
    color: #ef4444;
    font-family: 'JetBrains Mono', monospace;
    margin-top: 4px;
}

/* ── Section Headers ── */
.section-header {
    font-size: 11px;
    color: #6e7681;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin: 20px 0 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #21262d;
}

/* ── Metric Cards ── */
.metric-grid {
    display: flex;
    gap: 10px;
    margin-bottom: 16px;
    flex-wrap: wrap;
}
.metric-card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 10px 16px;
    flex: 1;
    min-width: 100px;
}
.metric-label {
    font-size: 10px;
    color: #6e7681;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 5px;
}
.metric-val {
    font-size: 16px;
    font-weight: 500;
    color: #e6edf3;
    font-family: 'JetBrains Mono', monospace;
}
.metric-val-pos { color: #22c55e; }
.metric-val-neg { color: #ef4444; }

/* ── Signal Badge ── */
.badge-buy  { display:inline-block; background:rgba(34,197,94,0.12); border:1px solid rgba(34,197,94,0.35); color:#22c55e; padding:5px 16px; border-radius:16px; font-size:13px; font-weight:600; letter-spacing:0.5px; }
.badge-sell { display:inline-block; background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.35); color:#ef4444; padding:5px 16px; border-radius:16px; font-size:13px; font-weight:600; letter-spacing:0.5px; }
.badge-hold { display:inline-block; background:rgba(234,179,8,0.12); border:1px solid rgba(234,179,8,0.35); color:#eab308; padding:5px 16px; border-radius:16px; font-size:13px; font-weight:600; letter-spacing:0.5px; }

/* ── News Cards ── */
.news-card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-left: 3px solid #21262d;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin-bottom: 8px;
}
.news-card.pos { border-left-color: #22c55e; }
.news-card.neg { border-left-color: #ef4444; }
.news-card.neu { border-left-color: #6e7681; }
.news-title { font-size: 13px; color: #c9d1d9; line-height: 1.5; }
.news-meta  { font-size: 11px; color: #6e7681; margin-top: 5px; font-family: 'JetBrains Mono', monospace; }

/* ── Sentiment Gauge ── */
.sent-block {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 16px 20px;
}
.sent-score-pos { font-size: 36px; font-weight: 300; color: #22c55e; font-family: 'JetBrains Mono', monospace; }
.sent-score-neg { font-size: 36px; font-weight: 300; color: #ef4444; font-family: 'JetBrains Mono', monospace; }
.sent-score-neu { font-size: 36px; font-weight: 300; color: #6e7681; font-family: 'JetBrains Mono', monospace; }

/* ── Buttons ── */
.stButton button {
    background: #0d1117 !important;
    border: 1px solid #30363d !important;
    color: #8b949e !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    padding: 3px 12px !important;
    transition: all 0.15s !important;
}
.stButton button:hover {
    background: #161b22 !important;
    color: #e6edf3 !important;
    border-color: #6e7681 !important;
}

/* ── Inputs ── */
.stTextInput input, .stSelectbox > div > div {
    background: #0d1117 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    font-family: 'JetBrains Mono', monospace !important;
    border-radius: 6px !important;
}

/* ── Refresh indicator ── */
.refresh-dot {
    display: inline-block;
    width: 7px; height: 7px;
    background: #22c55e;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

hr { border-color: #21262d !important; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════
#  DATA FUNCTIONS
# ══════════════════════════════════════════

@st.cache_data(ttl=60)
def fetch_index(symbol):
    """Fetch live index/ticker data."""
    try:
        t    = yf.Ticker(symbol)
        hist = t.history(period='2d', interval='1d')
        if len(hist) < 2:
            hist = t.history(period='5d', interval='1d')
        if hist.empty:
            return None
        cur   = float(hist['Close'].iloc[-1])
        prev  = float(hist['Close'].iloc[-2])
        chg   = cur - prev
        pct   = (chg / prev) * 100
        return {'price': cur, 'change': chg, 'pct': pct}
    except:
        return None


@st.cache_data(ttl=300)
def fetch_ohlcv(symbol, period='1y'):
    """Fetch OHLCV data and compute indicators."""
    try:
        t  = yf.Ticker(symbol)
        df = t.history(period=period, auto_adjust=True)
        if df.empty:
            return None
        df.reset_index(inplace=True)
        df['Date']    = pd.to_datetime(df['Date']).dt.tz_localize(None)
        df['SMA_50']  = df['Close'].rolling(50).mean()
        df['SMA_200'] = df['Close'].rolling(200).mean()
        df['RSI']     = compute_rsi(df['Close'])
        df['MACD'], df['Signal'] = compute_macd(df['Close'])
        return df
    except:
        return None


def compute_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))


def compute_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast).mean()
    ema_slow = series.ewm(span=slow).mean()
    macd     = ema_fast - ema_slow
    sig      = macd.ewm(span=signal).mean()
    return macd, sig


@st.cache_data(ttl=900)
def fetch_news_sentiment(query, api_key):
    """Fetch headlines and compute VADER sentiment."""
    analyzer  = SentimentIntensityAnalyzer()
    items     = []
    scores    = []
    try:
        url = (f'https://newsapi.org/v2/everything'
               f'?q={query}+stock+india'
               f'&language=en&sortBy=publishedAt&pageSize=20'
               f'&apiKey={api_key}')
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            for a in r.json().get('articles', [])[:10]:
                title = (a.get('title') or '').strip()
                if not title or title == '[Removed]':
                    continue
                score = analyzer.polarity_scores(title)['compound']
                items.append({
                    'title':  title,
                    'score':  score,
                    'source': (a.get('source') or {}).get('name', ''),
                    'url':    a.get('url', '')
                })
                scores.append(score)
    except:
        pass
    avg = float(np.mean(scores)) if scores else 0.0
    return avg, items


def get_trading_signal(df, sentiment):
    """Generate BUY/SELL/HOLD signal from technicals + sentiment."""
    if df is None or len(df) < 10:
        return 'HOLD'
    r      = df.iloc[-1]
    close  = r['Close']
    sma50  = r.get('SMA_50',  np.nan)
    sma200 = r.get('SMA_200', np.nan)
    rsi    = r.get('RSI',     50)
    macd   = r.get('MACD',    0)
    sig    = r.get('Signal',  0)

    bull = sum([
        close > sma50  if not np.isnan(sma50)  else False,
        close > sma200 if not np.isnan(sma200) else False,
        rsi < 70,
        macd > sig,
        sentiment > 0.05
    ])
    bear = sum([
        close < sma50  if not np.isnan(sma50)  else False,
        close < sma200 if not np.isnan(sma200) else False,
        rsi > 30,
        macd < sig,
        sentiment < -0.05
    ])
    if bull >= 4:
        return 'BUY'
    elif bear >= 4:
        return 'SELL'
    return 'HOLD'


def filter_range(df, key):
    end   = df['Date'].max()
    delta = {'1W': 7, '1M': 30, '3M': 90, '6M': 180, '1Y': 365, '3Y': 1095, '5Y': 1825}
    start = end - timedelta(days=delta.get(key, 365))
    return df[df['Date'] >= start].copy()


# ══════════════════════════════════════════
#  CHART BUILDER
# ══════════════════════════════════════════

def build_chart(df, chart_type, show_sma50, show_sma200, show_volume, show_rsi):
    rows       = 3 if show_rsi else 2
    row_h      = [0.6, 0.2, 0.2][:rows]
    fig        = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        row_heights=row_h,
        vertical_spacing=0.02
    )

    close_arr   = df['Close'].values
    is_pos      = close_arr[-1] >= close_arr[0]
    line_col    = '#22c55e' if is_pos else '#ef4444'
    fill_col    = 'rgba(34,197,94,0.07)' if is_pos else 'rgba(239,68,68,0.07)'

    # Price
    if chart_type == 'Candle':
        fig.add_trace(go.Candlestick(
            x=df['Date'], open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name='Price',
            increasing=dict(line=dict(color='#22c55e', width=1), fillcolor='rgba(34,197,94,0.8)'),
            decreasing=dict(line=dict(color='#ef4444', width=1), fillcolor='rgba(239,68,68,0.8)'),
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['Close'], name='Price',
            line=dict(color=line_col, width=1.6),
            fill='tozeroy', fillcolor=fill_col,
            hovertemplate='%{x|%d %b %Y}  ₹%{y:,.2f}<extra></extra>'
        ), row=1, col=1)

    if show_sma50:
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['SMA_50'], name='50 DMA',
            line=dict(color='#f59e0b', width=1, dash='dot'),
            hovertemplate='50D: ₹%{y:,.2f}<extra></extra>'
        ), row=1, col=1)

    if show_sma200:
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['SMA_200'], name='200 DMA',
            line=dict(color='#818cf8', width=1, dash='dot'),
            hovertemplate='200D: ₹%{y:,.2f}<extra></extra>'
        ), row=1, col=1)

    # Volume
    if show_volume:
        vol_col = ['rgba(34,197,94,0.5)' if c >= o else 'rgba(239,68,68,0.5)'
                   for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(
            x=df['Date'], y=df['Volume'], name='Volume',
            marker_color=vol_col,
            hovertemplate='Vol: %{y:,.0f}<extra></extra>'
        ), row=2, col=1)

    # RSI
    if show_rsi:
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['RSI'], name='RSI',
            line=dict(color='#38bdf8', width=1.2),
            hovertemplate='RSI: %{y:.1f}<extra></extra>'
        ), row=rows, col=1)
        fig.add_hline(y=70, line=dict(color='#ef4444', width=0.6, dash='dot'), row=rows, col=1)
        fig.add_hline(y=30, line=dict(color='#22c55e', width=0.6, dash='dot'), row=rows, col=1)

    fig.update_layout(
        plot_bgcolor='#080c14',
        paper_bgcolor='#080c14',
        font=dict(family='Inter', color='#6e7681', size=11),
        margin=dict(l=8, r=55, t=8, b=8),
        height=520,
        hovermode='x unified',
        hoverlabel=dict(bgcolor='#0d1117', bordercolor='#30363d',
                        font=dict(color='#e6edf3', size=12)),
        legend=dict(orientation='h', y=1.04, x=0,
                    bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#8b949e', size=11)),
        xaxis=dict(showgrid=False, zeroline=False, color='#6e7681',
                   rangeslider=dict(visible=False)),
        yaxis=dict(showgrid=True, gridcolor='rgba(33,38,45,0.9)',
                   zeroline=False, color='#6e7681',
                   side='right', tickprefix='₹', tickformat=',.0f'),
        yaxis2=dict(showgrid=False, zeroline=False, color='#6e7681', tickformat='.2s'),
    )
    if show_rsi:
        fig.update_layout(
            **{f'xaxis{rows}': dict(showgrid=False, color='#6e7681'),
               f'yaxis{rows}': dict(showgrid=True, gridcolor='rgba(33,38,45,0.7)',
                                    zeroline=False, color='#6e7681', range=[0, 100])}
        )
    return fig


# ══════════════════════════════════════════
#  APP
# ══════════════════════════════════════════

# Auto-refresh every 60 seconds
if AUTO_REFRESH:
    count = st_autorefresh(interval=60000, key='autorefresh')

# ── Session State ──
if 'range' not in st.session_state:
    st.session_state.range = '1Y'

# ── Header ──
h_left, h_right = st.columns([3, 1])
with h_left:
    now = datetime.now().strftime('%d %b %Y  %H:%M:%S')
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px">
        <span style="font-size:20px;font-weight:700;color:#e6edf3;letter-spacing:-0.5px">
            📈 MarketPulse India
        </span>
        <span style="font-size:11px;color:#6e7681;font-family:'JetBrains Mono',monospace">
            <span class="refresh-dot"></span>LIVE · {now}
        </span>
    </div>
    """, unsafe_allow_html=True)

with h_right:
    NEWSAPI_KEY = st.text_input('', placeholder='🔑 NewsAPI key', type='password',
                                 label_visibility='collapsed')

# ── Live Indices Ticker Bar ──
st.markdown('<div class="section-header">Market Indices</div>', unsafe_allow_html=True)

INDICES = {
    'NIFTY 50':    '^NSEI',
    'BANKNIFTY':   '^NSEBANK',
    'SENSEX':      '^BSESN',
    'BTC / USD':   'BTC-USD',
    'USD / INR':   'USDINR=X',
    'GOLD':        'GC=F',
}

cols = st.columns(len(INDICES))
for col, (name, sym) in zip(cols, INDICES.items()):
    data = fetch_index(sym)
    with col:
        if data:
            is_pos     = data['pct'] >= 0
            card_class = 'pos' if is_pos else 'neg'
            chg_class  = 'ticker-change-pos' if is_pos else 'ticker-change-neg'
            arrow      = '▲' if is_pos else '▼'
            prefix     = '₹' if 'INR' in name or 'NIFTY' in name or 'SENSEX' in name or 'BANK' in name else '$' if 'BTC' in name else ''
            fmt        = f'{prefix}{data["price"]:,.2f}'
            st.markdown(f"""
            <div class="ticker-card {card_class}">
                <div class="ticker-name">{name}</div>
                <div class="ticker-price">{fmt}</div>
                <div class="{chg_class}">{arrow} {abs(data['pct']):.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="ticker-card">
                <div class="ticker-name">{name}</div>
                <div class="ticker-price" style="color:#6e7681">—</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown('<hr>', unsafe_allow_html=True)

# ── Stock Selector ──
NIFTY100 = {
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS", "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS", "ICICI Bank": "ICICIBANK.NS",
    "State Bank of India": "SBIN.NS", "Axis Bank": "AXISBANK.NS",
    "Kotak Bank": "KOTAKBANK.NS", "Bajaj Finance": "BAJFINANCE.NS",
    "Bharti Airtel": "BHARTIARTL.NS", "ITC": "ITC.NS",
    "Larsen & Toubro": "LT.NS", "HCL Technologies": "HCLTECH.NS",
    "Wipro": "WIPRO.NS", "Asian Paints": "ASIANPAINT.NS",
    "Maruti Suzuki": "MARUTI.NS", "Sun Pharma": "SUNPHARMA.NS",
    "Titan": "TITAN.NS", "Nestle India": "NESTLEIND.NS",
    "NTPC": "NTPC.NS", "Power Grid": "POWERGRID.NS",
    "Coal India": "COALINDIA.NS", "ONGC": "ONGC.NS",
    "Tata Steel": "TATASTEEL.NS", "JSW Steel": "JSWSTEEL.NS",
    "Hindalco": "HINDALCO.NS", "Tata Motors": "TATAMOTORS.NS",
    "M&M": "M&M.NS", "Bajaj Auto": "BAJAJ-AUTO.NS",
    "Eicher Motors": "EICHERMOT.NS", "Tech Mahindra": "TECHM.NS",
    "Dr. Reddy's": "DRREDDY.NS", "Cipla": "CIPLA.NS",
    "Divi's Labs": "DIVISLAB.NS", "Apollo Hospitals": "APOLLOHOSP.NS",
    "DLF": "DLF.NS", "Tata Power": "TATAPOWER.NS",
    "Adani Ports": "ADANIPORTS.NS", "Adani Enterprises": "ADANIENT.NS",
    "HAL": "HAL.NS", "BEL": "BEL.NS",
    "IndiGo": "INDIGO.NS", "Avenue Supermarts": "DMART.NS",
    "Pidilite": "PIDILITIND.NS", "Grasim": "GRASIM.NS",
    "UltraTech Cement": "ULTRACEMCO.NS", "Shree Cement": "SHREECEM.NS",
    "Hindustan Unilever": "HINDUNILVR.NS", "Havells": "HAVELLS.NS",
    "Siemens": "SIEMENS.NS", "ABB India": "ABB.NS",
    "Trent": "TRENT.NS", "Zydus Life": "ZYDUSLIFE.NS",
    "Shriram Finance": "SHRIRAMFIN.NS", "Varun Beverages": "VBL.NS",
    "Vedanta": "VEDL.NS", "GAIL": "GAIL.NS",
    "BPCL": "BPCL.NS", "IOC": "IOC.NS",
    "PFC": "PFC.NS", "REC Ltd": "RECLTD.NS",
    "LIC": "LICI.NS", "SBI Life": "SBILIFE.NS",
    "HDFC Life": "HDFCLIFE.NS", "Bajaj Finserv": "BAJAJFINSV.NS",
}

sel_left, sel_mid, sel_right = st.columns([2, 1, 1])
with sel_left:
    selected_name = st.selectbox('Select Stock', list(NIFTY100.keys()),
                                  label_visibility='visible')
with sel_mid:
    custom_sym = st.text_input('Custom Symbol', placeholder='e.g. INFY.NS',
                                label_visibility='visible')
with sel_right:
    chart_type = st.selectbox('Chart Type', ['Line', 'Candle'],
                               label_visibility='visible')

symbol       = custom_sym.upper().strip() if custom_sym else NIFTY100[selected_name]
display_name = custom_sym.upper().strip() if custom_sym else selected_name

# ── Fetch Stock Data ──
with st.spinner(f'Loading {display_name}...'):
    df_full = fetch_ohlcv(symbol, '5y')

if df_full is None or df_full.empty:
    st.error(f'Could not load data for **{symbol}**. Check the ticker symbol.')
    st.stop()

# ── Price Header ──
latest       = df_full.iloc[-1]
prev         = df_full.iloc[-2]
cur_price    = latest['Close']
price_chg    = cur_price - prev['Close']
pct_chg      = (price_chg / prev['Close']) * 100
is_pos       = price_chg >= 0
arrow        = '▲' if is_pos else '▼'
price_color  = '#22c55e' if is_pos else '#ef4444'

col_price, col_metrics = st.columns([1, 3])
with col_price:
    st.markdown(f"""
    <div style="margin:8px 0 16px">
        <div style="font-size:13px;color:#6e7681;margin-bottom:4px">{display_name} · {symbol}</div>
        <div style="font-size:38px;font-weight:300;color:#e6edf3;font-family:'JetBrains Mono',monospace;letter-spacing:-1px">
            ₹{cur_price:,.2f}
        </div>
        <div style="font-size:15px;color:{price_color};margin-top:4px;font-family:'JetBrains Mono',monospace">
            {arrow} ₹{abs(price_chg):,.2f} &nbsp; ({abs(pct_chg):.2f}%)
        </div>
        <div style="font-size:11px;color:#6e7681;margin-top:6px">
            {latest['Date'].strftime('%d %b %Y')}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_metrics:
    sma50   = latest.get('SMA_50',  np.nan)
    sma200  = latest.get('SMA_200', np.nan)
    rsi_val = latest.get('RSI', np.nan)
    high52  = df_full['High'].tail(252).max()
    low52   = df_full['Low'].tail(252).min()
    avg_vol = df_full['Volume'].tail(30).mean()
    s50c    = 'metric-val-pos' if cur_price > sma50  else 'metric-val-neg'
    s200c   = 'metric-val-pos' if cur_price > sma200 else 'metric-val-neg'
    rsic    = 'metric-val-neg' if rsi_val > 70 else ('metric-val-pos' if rsi_val < 30 else 'metric-val')

    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">52W High</div>
            <div class="metric-val">₹{high52:,.0f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">52W Low</div>
            <div class="metric-val">₹{low52:,.0f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">50 DMA</div>
            <div class="metric-val {s50c}">₹{sma50:,.0f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">200 DMA</div>
            <div class="metric-val {s200c}">₹{sma200:,.0f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">RSI (14)</div>
            <div class="metric-val {rsic}">{rsi_val:.1f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Avg Vol 30D</div>
            <div class="metric-val">{avg_vol/1e6:.1f}M</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Chart Controls ──
ctrl_left, ctrl_right = st.columns([2, 1])
with ctrl_left:
    rcols = st.columns(7)
    for i, r in enumerate(['1W', '1M', '3M', '6M', '1Y', '3Y', '5Y']):
        with rcols[i]:
            if st.button(r, key=f'r_{r}', use_container_width=True):
                st.session_state.range = r
                st.rerun()

with ctrl_right:
    cc = st.columns(4)
    with cc[0]: show_50  = st.checkbox('50D',  value=True)
    with cc[1]: show_200 = st.checkbox('200D', value=True)
    with cc[2]: show_vol = st.checkbox('Vol',  value=True)
    with cc[3]: show_rsi = st.checkbox('RSI',  value=False)

# ── Main Chart ──
df_view = filter_range(df_full, st.session_state.range)
fig     = build_chart(df_view, chart_type, show_50, show_200, show_vol, show_rsi)
st.plotly_chart(fig, use_container_width=True, config={
    'displayModeBar': True,
    'modeBarButtonsToRemove': ['autoScale2d', 'lasso2d', 'select2d'],
    'displaylogo': False,
    'scrollZoom': True
})

st.markdown('<hr>', unsafe_allow_html=True)

# ── Bottom: Signal + Sentiment + News ──
bot_left, bot_mid, bot_right = st.columns([1, 1, 2])

# Sentiment fetch
sent_score = 0.0
news_items = []
if NEWSAPI_KEY:
    with st.spinner('Fetching news...'):
        sent_score, news_items = fetch_news_sentiment(display_name, NEWSAPI_KEY)

signal = get_trading_signal(df_view, sent_score)

with bot_left:
    st.markdown('<div class="section-header">Trading Signal</div>', unsafe_allow_html=True)
    badge = {
        'BUY':  '<span class="badge-buy">▲ &nbsp;BUY</span>',
        'SELL': '<span class="badge-sell">▼ &nbsp;SELL</span>',
        'HOLD': '<span class="badge-hold">◆ &nbsp;HOLD</span>'
    }[signal]
    st.markdown(badge, unsafe_allow_html=True)

    macd_v = latest.get('MACD',   0)
    sig_v  = latest.get('Signal', 0)
    trend  = '▲ Bullish' if cur_price > sma50 else '▼ Bearish'
    tcolor = '#22c55e' if cur_price > sma50 else '#ef4444'
    mc     = '#22c55e' if macd_v > sig_v else '#ef4444'

    st.markdown(f"""
    <div style="margin-top:16px;background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:14px 16px">
        <div style="display:flex;justify-content:space-between;margin-bottom:10px">
            <span style="font-size:11px;color:#6e7681">Trend</span>
            <span style="font-size:12px;color:{tcolor};font-weight:500">{trend}</span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:10px">
            <span style="font-size:11px;color:#6e7681">MACD</span>
            <span style="font-size:12px;color:{mc};font-family:'JetBrains Mono',monospace">{macd_v:.3f}</span>
        </div>
        <div style="display:flex;justify-content:space-between">
            <span style="font-size:11px;color:#6e7681">RSI</span>
            <span style="font-size:12px;color:#e6edf3;font-family:'JetBrains Mono',monospace">{rsi_val:.1f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with bot_mid:
    st.markdown('<div class="section-header">News Sentiment</div>', unsafe_allow_html=True)
    sc     = '#22c55e' if sent_score > 0.05 else ('#ef4444' if sent_score < -0.05 else '#6e7681')
    slabel = 'Positive' if sent_score > 0.05 else ('Negative' if sent_score < -0.05 else 'Neutral')
    sclass = 'sent-score-pos' if sent_score > 0.05 else ('sent-score-neg' if sent_score < -0.05 else 'sent-score-neu')
    spct   = int((sent_score + 1) / 2 * 100)

    st.markdown(f"""
    <div class="sent-block">
        <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:12px">
            <span class="{sclass}">{sent_score:+.3f}</span>
            <span style="font-size:13px;color:{sc};font-weight:500">{slabel}</span>
        </div>
        <div style="height:5px;background:#21262d;border-radius:3px;overflow:hidden;margin-bottom:8px">
            <div style="height:100%;width:{spct}%;background:{sc};border-radius:3px"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:10px;color:#6e7681">
            <span>Bearish</span><span>Neutral</span><span>Bullish</span>
        </div>
        <div style="margin-top:14px;font-size:11px;color:#6e7681">
            Based on {len(news_items)} headlines
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not NEWSAPI_KEY:
        st.markdown("""
        <div style="font-size:11px;color:#6e7681;margin-top:8px;text-align:center">
            Enter NewsAPI key to enable sentiment
        </div>
        """, unsafe_allow_html=True)

with bot_right:
    st.markdown('<div class="section-header">Latest News</div>', unsafe_allow_html=True)
    if news_items:
        for item in news_items[:5]:
            s  = item['score']
            cc = 'pos' if s > 0.05 else ('neg' if s < -0.05 else 'neu')
            sc2 = '#22c55e' if s > 0.05 else ('#ef4444' if s < -0.05 else '#6e7681')
            title = item['title'][:130] + ('...' if len(item['title']) > 130 else '')
            st.markdown(f"""
            <div class="news-card {cc}">
                <div class="news-title">{title}</div>
                <div class="news-meta">{item['source']} &nbsp;·&nbsp; <span style="color:{sc2}">{s:+.2f}</span></div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#0d1117;border:1px solid #21262d;border-radius:8px;
                    padding:30px;text-align:center;color:#6e7681;font-size:13px">
            Enter NewsAPI key to see latest headlines
        </div>
        """, unsafe_allow_html=True)

# ── Footer ──
st.markdown(f"""
<div style="margin-top:28px;padding-top:14px;border-top:1px solid #21262d;
            display:flex;justify-content:space-between;align-items:center">
    <span style="font-size:11px;color:#6e7681">
        MarketPulse India &nbsp;·&nbsp; NIFTY 100 Dashboard
    </span>
    <span style="font-size:11px;color:#6e7681">
        Data: Yahoo Finance &nbsp;·&nbsp; Refreshes every 60s &nbsp;·&nbsp; Not financial advice
    </span>
</div>
""", unsafe_allow_html=True)
