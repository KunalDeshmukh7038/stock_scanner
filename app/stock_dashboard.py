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

IS_EMBEDDED = os.environ.get('STREAMLIT_EMBEDDED_DASHBOARD') == '1'

if not IS_EMBEDDED:
    st.set_page_config(
        page_title='StockSense India',
        page_icon='📊',
        layout='wide',
        initial_sidebar_state='collapsed'
    )

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #0a0e1a; color: #e8eaf0; }
    .main .block-container { padding: 1.5rem 2rem; max-width: 1400px; }
    .stock-name { font-size: 28px; font-weight: 600; color: #f0f2f8; letter-spacing: -0.5px; }
    .stock-symbol { font-size: 14px; color: #6b7280; font-family: 'DM Mono', monospace; background: #1a1f2e; padding: 3px 8px; border-radius: 4px; }
    .current-price { font-size: 42px; font-weight: 300; color: #f0f2f8; font-family: 'DM Mono', monospace; letter-spacing: -1px; }
    .price-change-pos { font-size: 18px; color: #22c55e; font-weight: 500; margin-left: 12px; }
    .price-change-neg { font-size: 18px; color: #ef4444; font-weight: 500; margin-left: 12px; }
    .price-date { font-size: 12px; color: #4b5563; margin-top: 4px; font-family: 'DM Mono', monospace; }
    .metric-row { display: flex; gap: 12px; margin: 16px 0; flex-wrap: wrap; }
    .metric-card { background: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 12px 20px; min-width: 130px; flex: 1; }
    .metric-label { font-size: 11px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }
    .metric-value { font-size: 18px; font-weight: 500; color: #f0f2f8; font-family: 'DM Mono', monospace; }
    .metric-value-pos { color: #22c55e; }
    .metric-value-neg { color: #ef4444; }
    .signal-buy { display: inline-block; background: rgba(34,197,94,0.15); border: 1px solid rgba(34,197,94,0.4); color: #22c55e; padding: 6px 20px; border-radius: 20px; font-weight: 600; font-size: 14px; }
    .signal-sell { display: inline-block; background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.4); color: #ef4444; padding: 6px 20px; border-radius: 20px; font-weight: 600; font-size: 14px; }
    .signal-hold { display: inline-block; background: rgba(234,179,8,0.15); border: 1px solid rgba(234,179,8,0.4); color: #eab308; padding: 6px 20px; border-radius: 20px; font-weight: 600; font-size: 14px; }
    .sentiment-container { background: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 16px 20px; margin: 8px 0; }
    .sentiment-label { font-size: 11px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 10px; }
    .sentiment-bar-bg { height: 6px; background: #1f2937; border-radius: 3px; overflow: hidden; margin: 8px 0; }
    .stButton button { background: #111827 !important; border: 1px solid #1f2937 !important; color: #9ca3af !important; font-family: 'DM Sans', sans-serif !important; font-size: 13px !important; font-weight: 500 !important; padding: 4px 14px !important; border-radius: 6px !important; }
    .stButton button:hover { background: #1f2937 !important; color: #f0f2f8 !important; }
    .stTextInput input { background: #111827 !important; border: 1px solid #1f2937 !important; color: #f0f2f8 !important; font-family: 'DM Mono', monospace !important; border-radius: 8px !important; }
    .stSelectbox div { background: #111827 !important; color: #f0f2f8 !important; }
    hr { border-color: #1f2937 !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .section-title { font-size: 12px; color: #4b5563; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; margin-top: 20px; }
    .news-item { background: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; }
    .news-headline { font-size: 13px; color: #d1d5db; line-height: 1.5; }
    .news-score-pos { color: #22c55e; font-size: 12px; font-family: 'DM Mono', monospace; }
    .news-score-neg { color: #ef4444; font-size: 12px; font-family: 'DM Mono', monospace; }
    .news-score-neu { color: #6b7280; font-size: 12px; font-family: 'DM Mono', monospace; }
</style>
""", unsafe_allow_html=True)


# ── Data Functions ──
@st.cache_data(ttl=300)
def fetch_stock_data(symbol, period='5y'):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, auto_adjust=True)
        if df.empty:
            return None, None
        df.reset_index(inplace=True)
        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
        df['SMA_50']  = df['Close'].rolling(50).mean()
        df['SMA_200'] = df['Close'].rolling(200).mean()
        info = ticker.info
        return df, info
    except Exception as e:
        return None, None


@st.cache_data(ttl=1800)
def fetch_sentiment(company_name, newsapi_key):
    analyzer = SentimentIntensityAnalyzer()
    headlines = []
    scores = []
    try:
        url = f'https://newsapi.org/v2/everything?q={company_name}+stock&language=en&sortBy=publishedAt&pageSize=15&apiKey={newsapi_key}'
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            articles = r.json().get('articles', [])
            for a in articles[:10]:
                title = a.get('title', '')
                if title:
                    score = analyzer.polarity_scores(title)['compound']
                    headlines.append({'title': title, 'score': score})
                    scores.append(score)
    except:
        pass
    avg = np.mean(scores) if scores else 0.0
    return avg, headlines


def filter_by_range(df, range_key):
    today = df['Date'].max()
    ranges = {
        '1M':  today - timedelta(days=30),
        '6M':  today - timedelta(days=180),
        '1Y':  today - timedelta(days=365),
        '3Y':  today - timedelta(days=1095),
        '5Y':  today - timedelta(days=1825),
        'Max': df['Date'].min()
    }
    start = ranges.get(range_key, df['Date'].min())
    return df[df['Date'] >= start].copy()


def get_signal(df, sentiment):
    if len(df) < 5:
        return 'HOLD'
    latest = df.iloc[-1]
    sma50  = latest.get('SMA_50', np.nan)
    sma200 = latest.get('SMA_200', np.nan)
    close  = latest['Close']
    price_trend   = close > sma50  if not np.isnan(sma50)  else False
    long_trend    = close > sma200 if not np.isnan(sma200) else False
    recent_return = (close - df.iloc[-5]['Close']) / df.iloc[-5]['Close']
    if price_trend and long_trend and sentiment >= 0.05 and recent_return > -0.02:
        return 'BUY'
    elif not price_trend and not long_trend and sentiment <= -0.05 and recent_return < 0.02:
        return 'SELL'
    else:
        return 'HOLD'


def build_chart(df, show_price, show_sma50, show_sma200, show_volume, chart_type='Line'):
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.02
    )

    close_arr    = df['Close'].values
    start_price  = close_arr[0] if len(close_arr) > 0 else 0
    is_positive  = close_arr[-1] >= start_price if len(close_arr) > 0 else True
    line_color   = '#22c55e' if is_positive else '#ef4444'
    fill_color   = 'rgba(34,197,94,0.06)' if is_positive else 'rgba(239,68,68,0.06)'

    if show_price:
        if chart_type == 'Candle':
            fig.add_trace(go.Candlestick(
                x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Price',
                increasing=dict(line=dict(color='#22c55e', width=1), fillcolor='#22c55e'),
                decreasing=dict(line=dict(color='#ef4444', width=1), fillcolor='#ef4444'),
            ), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['Close'],
                name='Price',
                line=dict(color=line_color, width=1.8),
                fill='tozeroy',
                fillcolor=fill_color,
                hovertemplate='<b>%{x|%d %b %Y}</b><br>Price: ₹%{y:,.2f}<extra></extra>'
            ), row=1, col=1)

    if show_sma50 and 'SMA_50' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['SMA_50'],
            name='50 DMA',
            line=dict(color='#f59e0b', width=1.2, dash='dot'),
            hovertemplate='50 DMA: ₹%{y:,.2f}<extra></extra>'
        ), row=1, col=1)

    if show_sma200 and 'SMA_200' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['SMA_200'],
            name='200 DMA',
            line=dict(color='#a78bfa', width=1.2, dash='dot'),
            hovertemplate='200 DMA: ₹%{y:,.2f}<extra></extra>'
        ), row=1, col=1)

    if show_volume and 'Volume' in df.columns:
        vol_colors = [
            'rgba(34,197,94,0.5)' if c >= o else 'rgba(239,68,68,0.5)'
            for c, o in zip(df['Close'], df['Open'])
        ]
        fig.add_trace(go.Bar(
            x=df['Date'],
            y=df['Volume'],
            name='Volume',
            marker_color=vol_colors,
            hovertemplate='Vol: %{y:,.0f}<extra></extra>'
        ), row=2, col=1)

    fig.update_layout(
        plot_bgcolor='#0a0e1a',
        paper_bgcolor='#0a0e1a',
        font=dict(family='DM Sans', color='#6b7280', size=12),
        margin=dict(l=10, r=60, t=10, b=10),
        height=480,
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='#111827',
            bordercolor='#374151',
            font=dict(color='#f0f2f8', size=12, family='DM Sans')
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom', y=1.02,
            xanchor='left', x=0,
            bgcolor='rgba(0,0,0,0)',
            font=dict(color='#9ca3af', size=12)
        ),
        xaxis=dict(
            showgrid=False, zeroline=False,
            showline=False, color='#4b5563',
            rangeslider=dict(visible=False)
        ),
        xaxis2=dict(showgrid=False, zeroline=False, color='#4b5563'),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(31,41,55,0.8)',
            gridwidth=0.5,
            zeroline=False,
            color='#6b7280',
            side='right',
            tickprefix='₹',
            tickformat=',.0f'
        ),
        yaxis2=dict(
            showgrid=False, zeroline=False,
            color='#4b5563',
            tickformat='.2s'
        )
    )
    return fig


# ── NIFTY 100 Stock List ──
NIFTY100 = {
    "ABB India": "ABB.NS",
    "Adani Enterprises": "ADANIENT.NS",
    "Adani Ports": "ADANIPORTS.NS",
    "Adani Power": "ADANIPOWER.NS",
    "Ambuja Cements": "AMBUJACEM.NS",
    "Apollo Hospitals": "APOLLOHOSP.NS",
    "Asian Paints": "ASIANPAINT.NS",
    "Avenue Supermarts": "DMART.NS",
    "Axis Bank": "AXISBANK.NS",
    "Bajaj Auto": "BAJAJ-AUTO.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
    "Bajaj Finserv": "BAJAJFINSV.NS",
    "Bank of Baroda": "BANKBARODA.NS",
    "Bharat Electronics": "BEL.NS",
    "BPCL": "BPCL.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "Britannia": "BRITANNIA.NS",
    "Canara Bank": "CANBK.NS",
    "Cipla": "CIPLA.NS",
    "Coal India": "COALINDIA.NS",
    "DLF": "DLF.NS",
    "Divi's Labs": "DIVISLAB.NS",
    "Dr. Reddy's": "DRREDDY.NS",
    "Eicher Motors": "EICHERMOT.NS",
    "GAIL": "GAIL.NS",
    "Grasim Industries": "GRASIM.NS",
    "HCL Technologies": "HCLTECH.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "HDFC Life": "HDFCLIFE.NS",
    "Havells India": "HAVELLS.NS",
    "Hindalco": "HINDALCO.NS",
    "HAL": "HAL.NS",
    "Hindustan Unilever": "HINDUNILVR.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "ITC": "ITC.NS",
    "Indian Hotels": "INDHOTEL.NS",
    "Indian Oil": "IOC.NS",
    "Infosys": "INFY.NS",
    "IndiGo": "INDIGO.NS",
    "JSW Steel": "JSWSTEEL.NS",
    "Kotak Bank": "KOTAKBANK.NS",
    "LTIMindtree": "LTIM.NS",
    "Larsen & Toubro": "LT.NS",
    "LIC": "LICI.NS",
    "Mahindra & Mahindra": "M&M.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "NTPC": "NTPC.NS",
    "Nestle India": "NESTLEIND.NS",
    "ONGC": "ONGC.NS",
    "Pidilite": "PIDILITIND.NS",
    "Power Finance Corp": "PFC.NS",
    "Power Grid": "POWERGRID.NS",
    "Punjab National Bank": "PNB.NS",
    "REC Ltd": "RECLTD.NS",
    "Reliance Industries": "RELIANCE.NS",
    "SBI Life": "SBILIFE.NS",
    "Shree Cement": "SHREECEM.NS",
    "Shriram Finance": "SHRIRAMFIN.NS",
    "Siemens": "SIEMENS.NS",
    "Solar Industries": "SOLARINDS.NS",
    "State Bank of India": "SBIN.NS",
    "Sun Pharma": "SUNPHARMA.NS",
    "TVS Motor": "TVSMOTOR.NS",
    "TCS": "TCS.NS",
    "Tata Consumer": "TATACONSUM.NS",
    "Tata Power": "TATAPOWER.NS",
    "Tata Steel": "TATASTEEL.NS",
    "Tech Mahindra": "TECHM.NS",
    "Titan": "TITAN.NS",
    "Torrent Pharma": "TORNTPHARM.NS",
    "Trent": "TRENT.NS",
    "UltraTech Cement": "ULTRACEMCO.NS",
    "Varun Beverages": "VBL.NS",
    "Vedanta": "VEDL.NS",
    "Wipro": "WIPRO.NS",
    "Zydus Life": "ZYDUSLIFE.NS"
}

# ── Session State ──
if 'range' not in st.session_state:
    st.session_state.range = '1Y'

# ── Top Bar ──
top_left, top_right = st.columns([3, 1])
with top_left:
    st.markdown('<div style="font-size:22px;font-weight:600;color:#f0f2f8;margin-bottom:16px;">📊 StockSense India</div>', unsafe_allow_html=True)
with top_right:
    NEWSAPI_KEY = st.text_input('NewsAPI Key', type='password', placeholder='Enter NewsAPI key...')

# ── Stock Selector ──
col_search, col_select = st.columns([1, 3])
with col_search:
    custom = st.text_input('', placeholder='e.g. RELIANCE.NS', label_visibility='collapsed')
with col_select:
    selected_name = st.selectbox('', list(NIFTY100.keys()), label_visibility='collapsed',
                                  index=list(NIFTY100.keys()).index('Reliance Industries'))

symbol       = custom.upper().strip() if custom else NIFTY100[selected_name]
display_name = custom.upper().strip() if custom else selected_name

st.markdown('<hr>', unsafe_allow_html=True)

# ── Fetch Data ──
with st.spinner('Loading...'):
    df_full, info = fetch_stock_data(symbol)

if df_full is None or df_full.empty:
    st.error(f'Could not fetch data for **{symbol}**. Please check the symbol.')
    st.stop()

# ── Latest Values ──
df_view      = filter_by_range(df_full, st.session_state.range)
latest       = df_full.iloc[-1]
prev         = df_full.iloc[-2] if len(df_full) > 1 else latest
current_price = latest['Close']
price_change  = current_price - prev['Close']
pct_change    = (price_change / prev['Close']) * 100
is_positive   = price_change >= 0
change_class  = 'price-change-pos' if is_positive else 'price-change-neg'
change_arrow  = '▲' if is_positive else '▼'

# ── Header ──
st.markdown(f"""
<div style="display:flex;align-items:baseline;gap:16px;margin-bottom:4px">
    <span class="stock-name">{display_name}</span>
    <span class="stock-symbol">{symbol}</span>
</div>
<div style="margin:12px 0 20px">
    <span class="current-price">₹{current_price:,.2f}</span>
    <span class="{change_class}">{change_arrow} ₹{abs(price_change):,.2f} ({abs(pct_change):.2f}%)</span>
    <div class="price-date">As of {latest['Date'].strftime('%d %b %Y')}</div>
</div>
""", unsafe_allow_html=True)

# ── Metric Cards ──
high_52  = df_full['High'].tail(252).max()
low_52   = df_full['Low'].tail(252).min()
avg_vol  = df_full['Volume'].tail(30).mean()
sma50    = latest.get('SMA_50', np.nan)
sma200   = latest.get('SMA_200', np.nan)
sma50_class  = 'metric-value-pos' if current_price > sma50  else 'metric-value-neg'
sma200_class = 'metric-value-pos' if current_price > sma200 else 'metric-value-neg'

st.markdown(f"""
<div class="metric-row">
    <div class="metric-card">
        <div class="metric-label">52W High</div>
        <div class="metric-value">₹{high_52:,.0f}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">52W Low</div>
        <div class="metric-value">₹{low_52:,.0f}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">50 DMA</div>
        <div class="metric-value {sma50_class}">₹{sma50:,.0f}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">200 DMA</div>
        <div class="metric-value {sma200_class}">₹{sma200:,.0f}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Avg Vol (30D)</div>
        <div class="metric-value">{avg_vol/1e6:.1f}M</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Chart Controls ──
ctrl_left, ctrl_right = st.columns([2, 1])

with ctrl_left:
    range_cols = st.columns(6)
    for i, r in enumerate(['1M', '6M', '1Y', '3Y', '5Y', 'Max']):
        with range_cols[i]:
            if st.button(r, key=f'range_{r}', use_container_width=True):
                st.session_state.range = r
                st.rerun()

with ctrl_right:
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        chart_type = st.selectbox('', ['Line', 'Candle'], label_visibility='collapsed')
    with c2:
        show_price = st.checkbox('Price', value=True)
    with c3:
        show_50 = st.checkbox('50D', value=True)
    with c4:
        show_200 = st.checkbox('200D', value=True)
    with c5:
        show_vol = st.checkbox('Vol', value=True)

# ── Chart ──
df_view = filter_by_range(df_full, st.session_state.range)
fig = build_chart(df_view, show_price, show_50, show_200, show_vol, chart_type)
st.plotly_chart(fig, use_container_width=True, config={
    'displayModeBar': True,
    'modeBarButtonsToRemove': ['autoScale2d', 'lasso2d', 'select2d'],
    'displaylogo': False
})

# ── Bottom Section ──
left_col, right_col = st.columns([1, 1])

with left_col:
    sentiment_score = 0.0
    headlines = []
    if NEWSAPI_KEY:
        with st.spinner('Fetching sentiment...'):
            sentiment_score, headlines = fetch_sentiment(display_name, NEWSAPI_KEY)

    signal = get_signal(df_view, sentiment_score)
    signal_html = {
        'BUY':  '<span class="signal-buy">▲ BUY</span>',
        'SELL': '<span class="signal-sell">▼ SELL</span>',
        'HOLD': '<span class="signal-hold">◆ HOLD</span>'
    }[signal]

    st.markdown('<div class="section-title">Trading Signal</div>', unsafe_allow_html=True)
    st.markdown(signal_html, unsafe_allow_html=True)

    sent_pct   = int((sentiment_score + 1) / 2 * 100)
    sent_color = '#22c55e' if sentiment_score > 0.05 else ('#ef4444' if sentiment_score < -0.05 else '#eab308')
    sent_label = 'Positive' if sentiment_score > 0.05 else ('Negative' if sentiment_score < -0.05 else 'Neutral')

    st.markdown(f"""
    <div class="sentiment-container" style="margin-top:16px">
        <div class="sentiment-label">News Sentiment</div>
        <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-size:22px;font-weight:500;color:{sent_color};font-family:'DM Mono',monospace">
                {sentiment_score:+.3f}
            </span>
            <span style="font-size:13px;color:{sent_color}">{sent_label}</span>
        </div>
        <div class="sentiment-bar-bg">
            <div style="height:100%;width:{sent_pct}%;background:{sent_color};border-radius:3px"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:10px;color:#374151;margin-top:4px">
            <span>Bearish</span><span>Neutral</span><span>Bullish</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with right_col:
    st.markdown('<div class="section-title">Latest News</div>', unsafe_allow_html=True)
    if headlines:
        for item in headlines[:5]:
            score = item['score']
            score_class = 'news-score-pos' if score > 0.05 else ('news-score-neg' if score < -0.05 else 'news-score-neu')
            st.markdown(f"""
            <div class="news-item">
                <div class="news-headline">{item['title'][:120]}{'...' if len(item['title']) > 120 else ''}</div>
                <div class="{score_class}" style="margin-top:6px">{score:+.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="sentiment-container">
            <div style="color:#4b5563;font-size:13px;text-align:center;padding:20px 0">
                Enter NewsAPI key above to see latest news
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
<div style="margin-top:32px;padding-top:16px;border-top:1px solid #1f2937;
            display:flex;justify-content:space-between">
    <span style="font-size:11px;color:#374151">StockSense India • NIFTY 100</span>
    <span style="font-size:11px;color:#374151">Data via Yahoo Finance • Not financial advice</span>
</div>
""", unsafe_allow_html=True)
