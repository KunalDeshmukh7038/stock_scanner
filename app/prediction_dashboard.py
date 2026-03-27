import os
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import joblib
import json
import finnhub
import requests
import plotly.graph_objects as go
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from pygooglenews import GoogleNews
from newsapi import NewsApiClient
import warnings
warnings.filterwarnings('ignore')

# ── Page Config ──
IS_EMBEDDED = os.environ.get('STREAMLIT_EMBEDDED_DASHBOARD') == '1'

if not IS_EMBEDDED:
    st.set_page_config(
        page_title='Sentiment Stock Prediction',
        page_icon='📈',
        layout='wide'
    )

# ── CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #080c14; color: #c9d1d9; }
.main .block-container { padding: 1.5rem 2rem; max-width: 1400px; }
.metric-card { background: #0d1117; border: 1px solid #21262d; border-radius: 10px; padding: 14px 18px; }
.metric-label { font-size: 11px; color: #6e7681; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }
.metric-value { font-size: 20px; font-weight: 500; color: #e6edf3; font-family: 'JetBrains Mono', monospace; }
.badge-buy  { display:inline-block; background:rgba(34,197,94,0.12); border:1px solid rgba(34,197,94,0.35); color:#22c55e; padding:8px 24px; border-radius:20px; font-size:16px; font-weight:600; }
.badge-sell { display:inline-block; background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.35); color:#ef4444; padding:8px 24px; border-radius:20px; font-size:16px; font-weight:600; }
.badge-hold { display:inline-block; background:rgba(234,179,8,0.12); border:1px solid rgba(234,179,8,0.35); color:#eab308; padding:8px 24px; border-radius:20px; font-size:16px; font-weight:600; }
.news-card { background:#0d1117; border:1px solid #21262d; border-left:3px solid #21262d; border-radius:0 8px 8px 0; padding:10px 14px; margin-bottom:8px; }
.news-card.pos { border-left-color:#22c55e; }
.news-card.neg { border-left-color:#ef4444; }
.news-card.neu { border-left-color:#6e7681; }
.news-title { font-size:13px; color:#c9d1d9; line-height:1.5; }
.news-meta  { font-size:11px; color:#6e7681; margin-top:5px; font-family:'JetBrains Mono',monospace; }
.section-header { font-size:11px; color:#6e7681; text-transform:uppercase; letter-spacing:1.2px; margin:20px 0 12px; padding-bottom:8px; border-bottom:1px solid #21262d; }
.stButton button { background:#0d1117 !important; border:1px solid #30363d !important; color:#8b949e !important; border-radius:6px !important; }
.stButton button:hover { background:#161b22 !important; color:#e6edf3 !important; }
hr { border-color: #21262d !important; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── API Keys (paste yours here) ──
NEWSAPI_KEY   = '2f1d92428deb43bbb3bcba707adb467d'
FINNHUB_KEY   = 'd6ufa6hr01qp1k9caodgd6ufa6hr01qp1k9caoe0'
MARKETAUX_KEY = 'UVGeywaTfEUoGbVvb0svGcTsZriJvvjeMmDSlisK'

# ── Load Model ──
@st.cache_resource
def load_model():
    try:
        model = joblib.load('models/xgb_upgraded_small.pkl')
        with open('models/feature_cols_upgraded.json') as f:
            features = json.load(f)
        return model, features
    except:
        model = joblib.load('models/xgb_small_model.pkl')
        with open('models/feature_cols_best.json') as f:
            features = json.load(f)
        return model, features

model, FEATURE_COLS = load_model()
analyzer = SentimentIntensityAnalyzer()

# ── Stock List ──
NIFTY100 = {
    "ABB India Ltd."                  : "ABB.NS",
    "Adani Enterprises Ltd."          : "ADANIENT.NS",
    "Adani Ports"                     : "ADANIPORTS.NS",
    "Adani Power Ltd."                : "ADANIPOWER.NS",
    "Ambuja Cements Ltd."             : "AMBUJACEM.NS",
    "Apollo Hospitals"                : "APOLLOHOSP.NS",
    "Asian Paints Ltd."               : "ASIANPAINT.NS",
    "Avenue Supermarts Ltd."          : "DMART.NS",
    "Axis Bank Ltd."                  : "AXISBANK.NS",
    "Bajaj Auto Ltd."                 : "BAJAJ-AUTO.NS",
    "Bajaj Finance Ltd."              : "BAJFINANCE.NS",
    "Bajaj Finserv Ltd."              : "BAJAJFINSV.NS",
    "Bank of Baroda"                  : "BANKBARODA.NS",
    "Bharat Electronics Ltd."         : "BEL.NS",
    "BPCL"                            : "BPCL.NS",
    "Bharti Airtel Ltd."              : "BHARTIARTL.NS",
    "Britannia Industries Ltd."       : "BRITANNIA.NS",
    "Canara Bank"                     : "CANBK.NS",
    "Cipla Ltd."                      : "CIPLA.NS",
    "Coal India Ltd."                 : "COALINDIA.NS",
    "DLF Ltd."                        : "DLF.NS",
    "Divi's Laboratories Ltd."        : "DIVISLAB.NS",
    "Dr. Reddy's Laboratories Ltd."   : "DRREDDY.NS",
    "Eicher Motors Ltd."              : "EICHERMOT.NS",
    "GAIL (India) Ltd."               : "GAIL.NS",
    "Grasim Industries Ltd."          : "GRASIM.NS",
    "HCL Technologies Ltd."           : "HCLTECH.NS",
    "HDFC Bank Ltd."                  : "HDFCBANK.NS",
    "HDFC Life Insurance"             : "HDFCLIFE.NS",
    "Havells India Ltd."              : "HAVELLS.NS",
    "Hindalco Industries Ltd."        : "HINDALCO.NS",
    "HAL"                             : "HAL.NS",
    "Hindustan Unilever Ltd."         : "HINDUNILVR.NS",
    "ICICI Bank Ltd."                 : "ICICIBANK.NS",
    "ITC Ltd."                        : "ITC.NS",
    "Indian Hotels Co. Ltd."          : "INDHOTEL.NS",
    "Indian Oil Corporation Ltd."     : "IOC.NS",
    "Infosys Ltd."                    : "INFY.NS",
    "IndiGo"                          : "INDIGO.NS",
    "JSW Steel Ltd."                  : "JSWSTEEL.NS",
    "Kotak Mahindra Bank Ltd."        : "KOTAKBANK.NS",
    "LTIMindtree Ltd."                : "LTIM.NS",
    "Larsen & Toubro Ltd."            : "LT.NS",
    "LIC"                             : "LICI.NS",
    "Mahindra & Mahindra Ltd."        : "M&M.NS",
    "Maruti Suzuki India Ltd."        : "MARUTI.NS",
    "NTPC Ltd."                       : "NTPC.NS",
    "Nestle India Ltd."               : "NESTLEIND.NS",
    "ONGC"                            : "ONGC.NS",
    "Pidilite Industries Ltd."        : "PIDILITIND.NS",
    "Power Finance Corporation Ltd."  : "PFC.NS",
    "Power Grid Corporation"          : "POWERGRID.NS",
    "Punjab National Bank"            : "PNB.NS",
    "REC Ltd."                        : "RECLTD.NS",
    "Reliance Industries Ltd."        : "RELIANCE.NS",
    "SBI Life Insurance"              : "SBILIFE.NS",
    "Shree Cement Ltd."               : "SHREECEM.NS",
    "Shriram Finance Ltd."            : "SHRIRAMFIN.NS",
    "Siemens Ltd."                    : "SIEMENS.NS",
    "Solar Industries India Ltd."     : "SOLARINDS.NS",
    "State Bank of India"             : "SBIN.NS",
    "Sun Pharmaceutical"              : "SUNPHARMA.NS",
    "TVS Motor Company Ltd."          : "TVSMOTOR.NS",
    "TCS"                             : "TCS.NS",
    "Tata Consumer Products Ltd."     : "TATACONSUM.NS",
    "Tata Power Co. Ltd."             : "TATAPOWER.NS",
    "Tata Steel Ltd."                 : "TATASTEEL.NS",
    "Tech Mahindra Ltd."              : "TECHM.NS",
    "Titan Company Ltd."              : "TITAN.NS",
    "Torrent Pharmaceuticals Ltd."    : "TORNTPHARM.NS",
    "Trent Ltd."                      : "TRENT.NS",
    "UltraTech Cement Ltd."           : "ULTRACEMCO.NS",
    "Varun Beverages Ltd."            : "VBL.NS",
    "Vedanta Ltd."                    : "VEDL.NS",
    "Wipro Ltd."                      : "WIPRO.NS",
    "Zydus Lifesciences Ltd."         : "ZYDUSLIFE.NS"
}


# ── Helper Functions ──
def get_stock_data(symbol):
    df = yf.download(symbol, start='2020-01-01',
                     auto_adjust=False, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.reset_index(inplace=True)
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    return df


def add_features(df):
    df['Return']       = df['Close'].pct_change()
    df['SMA_10']       = df['Close'].rolling(10).mean()
    df['SMA_20']       = df['Close'].rolling(20).mean()
    df['RSI']          = ta.momentum.RSIIndicator(df['Close'], 14).rsi()
    macd               = ta.trend.MACD(df['Close'])
    df['MACD']         = macd.macd()
    df['MACD_signal']  = macd.macd_signal()
    bb                 = ta.volatility.BollingerBands(df['Close'], 20, 2)
    df['BB_upper']     = bb.bollinger_hband()
    df['BB_lower']     = bb.bollinger_lband()
    df['BB_width']     = df['BB_upper'] - df['BB_lower']
    df['BB_pct']       = (df['Close'] - df['BB_lower']) / (df['BB_width'] + 1e-9)
    df['ATR']          = ta.volatility.AverageTrueRange(
                             df['High'], df['Low'], df['Close'], 14
                         ).average_true_range()
    df['Momentum']     = df['Close'] - df['Close'].shift(10)
    df['Volatility']   = df['Close'].rolling(10).std()
    df['Price_chg_5d'] = df['Close'].pct_change(5)
    df['Vol_MA_10']    = df['Volume'].rolling(10).mean()
    df['Volume_change']= df['Volume'].pct_change()
    df.dropna(inplace=True)
    return df


@st.cache_data(ttl=1800)
def get_sentiment(company_name):
    scores   = []
    all_news = []

    # ── NewsAPI ──
    try:
        newsapi   = NewsApiClient(api_key=NEWSAPI_KEY)
        articles  = newsapi.get_everything(
            q=company_name, language='en',
            sort_by='publishedAt', page_size=10
        )
        for a in articles['articles']:
            title = a.get('title', '')
            if title:
                score = analyzer.polarity_scores(title)['compound']
                scores.append(score)
                all_news.append({'title': title, 'score': score, 'source': 'NewsAPI'})
    except:
        pass

    # ── Google News ──
    try:
        gn     = GoogleNews(country='IN', lang='en')
        search = gn.search(company_name + ' stock', when='3d')
        for entry in search['entries'][:8]:
            title = entry.get('title', '')
            score = analyzer.polarity_scores(title)['compound']
            scores.append(score)
            all_news.append({'title': title, 'score': score, 'source': 'Google News'})
    except:
        pass

    # ── Finnhub General News ──
    try:
        fc   = finnhub.Client(api_key=FINNHUB_KEY)
        news = fc.general_news('general', min_id=0)
        company_lower = company_name.lower()
        for article in news[:50]:
            headline = article.get('headline', '').lower()
            if any(word in headline for word in company_lower.split()[:2]):
                score = analyzer.polarity_scores(article['headline'])['compound']
                scores.append(score)
                all_news.append({
                    'title' : article['headline'],
                    'score' : score,
                    'source': 'Finnhub'
                })
    except:
        pass

    # ── Marketaux ──
    try:
        url = (f'https://api.marketaux.com/v1/news/all'
               f'?search={company_name}'
               f'&language=en'
               f'&api_token={MARKETAUX_KEY}')
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            for a in r.json().get('data', []):
                title = a.get('title', '')
                score = analyzer.polarity_scores(title)['compound']
                scores.append(score)
                all_news.append({
                    'title' : title,
                    'score' : score,
                    'source': 'Marketaux'
                })
    except:
        pass

    avg_score = float(np.mean(scores)) if scores else 0.0
    return avg_score, all_news


# ── App UI ──
st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
    <span style="font-size:24px;font-weight:700;color:#e6edf3">
        📈 Sentiment-Driven Stock Prediction
    </span>
    <span style="font-size:12px;color:#6e7681;background:#0d1117;
                 padding:3px 10px;border-radius:12px;border:1px solid #21262d">
        NIFTY 100 · Indian Market
    </span>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──
st.sidebar.markdown('### ⚙️ Settings')
selected_name   = st.sidebar.selectbox('Select Stock', list(NIFTY100.keys()))
selected_symbol = NIFTY100[selected_name]
run_btn         = st.sidebar.button('🔮 Run Prediction', use_container_width=True)

st.sidebar.markdown('---')
st.sidebar.markdown('### 📊 Model Info')
st.sidebar.markdown(f"""
- **Model**: XGBoost + Sentiment
- **Features**: {len(FEATURE_COLS)}
- **Sources**: NewsAPI + Google + Finnhub + Marketaux
- **Accuracy**: ~51.57%
""")

if run_btn:
    # ── Fetch Data ──
    with st.spinner('Fetching stock data...'):
        df = get_stock_data(selected_symbol)
        df = add_features(df)

    # ── Fetch Sentiment ──
    with st.spinner('Analyzing sentiment from 4 sources...'):
        sentiment_score, news_items = get_sentiment(selected_name)

    # ── Prepare Features ──
    df['Sentiment_score'] = sentiment_score
    X = df[FEATURE_COLS].tail(1)
    X = X.replace([float('inf'), float('-inf')], float('nan'))
    X = X.fillna(X.median())

    # ── Predict ──
    prediction  = model.predict(X)[0]
    probability = model.predict_proba(X)[0][prediction]
    latest      = df.iloc[-1]

    # ── Signal ──
    price_above_sma20  = latest['Close'] > latest['SMA_20']
    price_below_sma20  = latest['Close'] < latest['SMA_20']
    rsi_not_overbought = latest['RSI'] < 70
    rsi_not_oversold   = latest['RSI'] > 30
    macd_positive      = latest['MACD'] > latest['MACD_signal']
    macd_negative      = latest['MACD'] < latest['MACD_signal']

    if (prediction == 1 and rsi_not_overbought
            and price_above_sma20 and macd_positive):
        signal      = 'BUY'
        badge       = '<span class="badge-buy">▲ &nbsp;BUY</span>'
    elif (prediction == 0 and rsi_not_oversold
            and price_below_sma20 and macd_negative):
        signal      = 'SELL'
        badge       = '<span class="badge-sell">▼ &nbsp;SELL</span>'
    else:
        signal      = 'HOLD'
        badge       = '<span class="badge-hold">◆ &nbsp;HOLD</span>'

    # ── Top Metrics ──
    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        ('Current Price',  f"₹{latest['Close']:.2f}"),
        ('Prediction',     '📈 UP' if prediction == 1 else '📉 DOWN'),
        ('Confidence',     f'{probability*100:.1f}%'),
        ('Sentiment',      f'{sentiment_score:+.3f}'),
        ('News Sources',   f'{len(news_items)} headlines'),
    ]
    for col, (label, value) in zip([c1,c2,c3,c4,c5], metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # ── Signal Badge ──
    st.markdown(f'### Trading Signal &nbsp; {badge}',
                unsafe_allow_html=True)

    st.markdown('<hr>', unsafe_allow_html=True)

    # ── Chart + Sentiment ──
    chart_col, sent_col = st.columns([2, 1])

    with chart_col:
        st.markdown('<div class="section-header">Price Chart — Last 100 Days</div>',
                    unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df['Date'].tail(100),
            open=df['Open'].tail(100),
            high=df['High'].tail(100),
            low=df['Low'].tail(100),
            close=df['Close'].tail(100),
            name='Price',
            increasing=dict(line=dict(color='#22c55e'), fillcolor='rgba(34,197,94,0.8)'),
            decreasing=dict(line=dict(color='#ef4444'), fillcolor='rgba(239,68,68,0.8)')
        ))
        fig.add_trace(go.Scatter(
            x=df['Date'].tail(100),
            y=df['SMA_20'].tail(100),
            name='SMA 20',
            line=dict(color='#f59e0b', width=1, dash='dot')
        ))
        fig.update_layout(
            plot_bgcolor='#080c14',
            paper_bgcolor='#080c14',
            font=dict(color='#6e7681'),
            height=380,
            margin=dict(l=8, r=8, t=8, b=8),
            xaxis=dict(showgrid=False, rangeslider=dict(visible=False),
                       color='#6e7681'),
            yaxis=dict(showgrid=True, gridcolor='#21262d',
                       side='right', tickprefix='₹', color='#6e7681'),
            legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#8b949e')),
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True,
                        config={'displaylogo': False})

    with sent_col:
        st.markdown('<div class="section-header">Sentiment Analysis</div>',
                    unsafe_allow_html=True)

        sent_color = ('#22c55e' if sentiment_score > 0.05
                      else '#ef4444' if sentiment_score < -0.05 else '#6e7681')
        sent_label = ('Bullish 📈' if sentiment_score > 0.05
                      else 'Bearish 📉' if sentiment_score < -0.05 else 'Neutral ➡️')
        sent_pct   = int((sentiment_score + 1) / 2 * 100)

        # Gauge chart
        fig2 = go.Figure(go.Indicator(
            mode='gauge+number',
            value=sentiment_score,
            number=dict(font=dict(color=sent_color, size=28)),
            title=dict(text=sent_label,
                       font=dict(color=sent_color, size=14)),
            gauge=dict(
                axis=dict(range=[-1, 1], tickcolor='#6e7681',
                          tickfont=dict(color='#6e7681')),
                bar=dict(color=sent_color),
                bgcolor='#0d1117',
                bordercolor='#21262d',
                steps=[
                    dict(range=[-1, -0.05], color='rgba(239,68,68,0.15)'),
                    dict(range=[-0.05, 0.05], color='rgba(110,118,129,0.15)'),
                    dict(range=[0.05, 1],  color='rgba(34,197,94,0.15)')
                ]
            )
        ))
        fig2.update_layout(
            plot_bgcolor='#080c14',
            paper_bgcolor='#080c14',
            height=240,
            margin=dict(l=20, r=20, t=30, b=10)
        )
        st.plotly_chart(fig2, use_container_width=True,
                        config={'displaylogo': False})

        # Source breakdown
        sources = {}
        for item in news_items:
            src = item.get('source', 'Unknown')
            sources[src] = sources.get(src, 0) + 1

        st.markdown('<div style="margin-top:8px">', unsafe_allow_html=True)
        for src, count in sources.items():
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;
                        padding:6px 0;border-bottom:1px solid #21262d">
                <span style="font-size:12px;color:#8b949e">{src}</span>
                <span style="font-size:12px;color:#e6edf3;
                             font-family:'JetBrains Mono',monospace">
                    {count} headlines
                </span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Technical Indicators ──
    st.markdown('<div class="section-header">Technical Indicators</div>',
                unsafe_allow_html=True)
    t1, t2, t3, t4, t5, t6 = st.columns(6)
    indicators = [
        ('RSI',        f"{latest['RSI']:.2f}"),
        ('MACD',       f"{latest['MACD']:.3f}"),
        ('SMA 10',     f"₹{latest['SMA_10']:.2f}"),
        ('SMA 20',     f"₹{latest['SMA_20']:.2f}"),
        ('ATR',        f"{latest['ATR']:.2f}"),
        ('Volatility', f"{latest['Volatility']:.2f}"),
    ]
    for col, (label, value) in zip([t1,t2,t3,t4,t5,t6], indicators):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="font-size:16px">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── News Headlines ──
    st.markdown('<div class="section-header">Latest News Headlines</div>',
                unsafe_allow_html=True)

    if news_items:
        for item in news_items[:6]:
            s  = item['score']
            cc = 'pos' if s > 0.05 else ('neg' if s < -0.05 else 'neu')
            sc = '#22c55e' if s > 0.05 else ('#ef4444' if s < -0.05 else '#6e7681')
            title = item['title'][:140] + ('...' if len(item['title']) > 140 else '')
            st.markdown(f"""
            <div class="news-card {cc}">
                <div class="news-title">{title}</div>
                <div class="news-meta">
                    {item.get('source','Unknown')} &nbsp;·&nbsp;
                    <span style="color:{sc}">{s:+.3f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info('No news headlines found. Check API keys.')

else:
    # ── Welcome Screen ──
    st.markdown("""
    <div style="text-align:center;padding:60px 20px">
        <div style="font-size:64px;margin-bottom:16px">📈</div>
        <div style="font-size:24px;font-weight:600;color:#e6edf3;margin-bottom:8px">
            Sentiment-Driven Stock Prediction
        </div>
        <div style="font-size:15px;color:#6e7681;margin-bottom:32px">
            Select a stock from the sidebar and click Run Prediction
        </div>
        <div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap">
            <div style="background:#0d1117;border:1px solid #21262d;border-radius:10px;padding:16px 24px">
                <div style="font-size:24px;font-weight:700;color:#22c55e">99</div>
                <div style="font-size:12px;color:#6e7681">NIFTY Stocks</div>
            </div>
            <div style="background:#0d1117;border:1px solid #21262d;border-radius:10px;padding:16px 24px">
                <div style="font-size:24px;font-weight:700;color:#38bdf8">4</div>
                <div style="font-size:12px;color:#6e7681">News Sources</div>
            </div>
            <div style="background:#0d1117;border:1px solid #21262d;border-radius:10px;padding:16px 24px">
                <div style="font-size:24px;font-weight:700;color:#f59e0b">21</div>
                <div style="font-size:12px;color:#6e7681">Features</div>
            </div>
            <div style="background:#0d1117;border:1px solid #21262d;border-radius:10px;padding:16px 24px">
                <div style="font-size:24px;font-weight:700;color:#a78bfa">51.57%</div>
                <div style="font-size:12px;color:#6e7681">Model Accuracy</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
