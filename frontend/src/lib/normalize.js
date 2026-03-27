const stockKeys = {
  symbol: ['symbol', 'ticker', 'stock_symbol', 'Symbol'],
  companyName: ['company_name', 'companyName', 'name', 'stock_name', 'company'],
  sector: ['sector', 'industry', 'segment'],
  price: ['current_price', 'price', 'close', 'ltp', 'Current Price'],
  changePct: ['change_pct', 'changePercent', 'pct_change', 'day_change_pct', 'Change %'],
  rsi: ['rsi', 'RSI', 'rsi_14'],
  macd: ['macd', 'MACD'],
  sentimentScore: ['sentiment_score', 'sentiment', 'news_sentiment', 'Sentiment_score'],
  signal: ['signal', 'ai_signal', 'trading_signal'],
  prediction: ['prediction', 'ai_prediction', 'direction'],
  confidence: ['confidence', 'confidence_pct', 'probability'],
  marketCap: ['market_cap', 'marketCap', 'Market Cap'],
  pe: ['pe', 'pe_ratio', 'P/E', 'peRatio'],
  bookValue: ['book_value', 'bookValue', 'Book Value'],
  roe: ['roe', 'ROE'],
  roce: ['roce', 'ROCE'],
  dividendYield: ['dividend_yield', 'dividendYield', 'Dividend Yield'],
  faceValue: ['face_value', 'faceValue', 'Face Value'],
  high: ['high', 'day_high', 'High'],
  low: ['low', 'day_low', 'Low'],
  weekHigh52: ['high_52w', 'week52High', '52w_high'],
  weekLow52: ['low_52w', 'week52Low', '52w_low'],
};

function firstDefined(obj, keys, fallback = null) {
  if (!obj) return fallback;

  for (const key of keys) {
    if (obj[key] !== undefined && obj[key] !== null && obj[key] !== '') {
      return obj[key];
    }
  }

  return fallback;
}

function numeric(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function numericOrNull(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function stringValue(value, fallback = '-') {
  return value === undefined || value === null || value === '' ? fallback : String(value);
}

function toArray(value) {
  if (Array.isArray(value)) return value;
  if (Array.isArray(value?.items)) return value.items;
  if (Array.isArray(value?.results)) return value.results;
  if (Array.isArray(value?.data)) return value.data;
  return [];
}

function normalizeSignal(signal, prediction) {
  const raw = String(signal || prediction || 'HOLD').toUpperCase();
  if (raw.includes('BUY')) return 'BUY';
  if (raw.includes('SELL') || raw.includes('DOWN')) return 'SELL';
  if (raw.includes('UP')) return 'BUY';
  return 'HOLD';
}

function normalizePrediction(prediction, signal) {
  const raw = String(prediction || signal || '').toUpperCase();
  if (raw.includes('UP') || raw.includes('BUY')) return 'UP';
  if (raw.includes('DOWN') || raw.includes('SELL')) return 'DOWN';
  return 'HOLD';
}

export function normalizeStock(item = {}) {
  const summary = item.summary || {};
  const fundamentals = item.fundamentals || summary.fundamentals || {};
  const metrics = { ...fundamentals, ...(item.metrics || {}), ...summary };

  const symbol = stringValue(firstDefined(item, stockKeys.symbol, firstDefined(metrics, stockKeys.symbol)));
  const companyName = stringValue(
    firstDefined(item, stockKeys.companyName, firstDefined(metrics, stockKeys.companyName, symbol)),
    symbol,
  );

  const signal = normalizeSignal(
    firstDefined(item, stockKeys.signal, firstDefined(metrics, stockKeys.signal)),
    firstDefined(item, stockKeys.prediction, firstDefined(metrics, stockKeys.prediction)),
  );

  const prediction = normalizePrediction(
    firstDefined(item, stockKeys.prediction, firstDefined(metrics, stockKeys.prediction)),
    signal,
  );

  return {
    raw: item,
    symbol,
    companyName,
    sector: stringValue(firstDefined(item, stockKeys.sector, firstDefined(metrics, stockKeys.sector)), 'Unclassified'),
    price: numeric(firstDefined(item, stockKeys.price, firstDefined(metrics, stockKeys.price))),
    changePct: numeric(firstDefined(item, stockKeys.changePct, firstDefined(metrics, stockKeys.changePct))),
    rsi: numeric(firstDefined(item, stockKeys.rsi, firstDefined(metrics, stockKeys.rsi))),
    macd: numeric(firstDefined(item, stockKeys.macd, firstDefined(metrics, stockKeys.macd))),
    sentimentScore: numeric(
      firstDefined(item, stockKeys.sentimentScore, firstDefined(metrics, stockKeys.sentimentScore)),
    ),
    signal,
    prediction,
    confidence: numeric(firstDefined(item, stockKeys.confidence, firstDefined(metrics, stockKeys.confidence))) * 100 > 100
      ? numeric(firstDefined(item, stockKeys.confidence, firstDefined(metrics, stockKeys.confidence)))
      : numeric(firstDefined(item, stockKeys.confidence, firstDefined(metrics, stockKeys.confidence))) * 100,
    marketCap: numeric(firstDefined(item, stockKeys.marketCap, firstDefined(metrics, stockKeys.marketCap))),
    pe: numeric(firstDefined(item, stockKeys.pe, firstDefined(metrics, stockKeys.pe))),
    bookValue: numeric(firstDefined(item, stockKeys.bookValue, firstDefined(metrics, stockKeys.bookValue))),
    roe: numericOrNull(firstDefined(item, stockKeys.roe, firstDefined(metrics, stockKeys.roe))),
    roce: numericOrNull(firstDefined(item, stockKeys.roce, firstDefined(metrics, stockKeys.roce))),
    dividendYield: numericOrNull(
      firstDefined(item, stockKeys.dividendYield, firstDefined(metrics, stockKeys.dividendYield)),
    ),
    faceValue: numericOrNull(firstDefined(item, stockKeys.faceValue, firstDefined(metrics, stockKeys.faceValue))),
    high: numeric(firstDefined(item, stockKeys.high, firstDefined(metrics, stockKeys.high))),
    low: numeric(firstDefined(item, stockKeys.low, firstDefined(metrics, stockKeys.low))),
    weekHigh52: numeric(firstDefined(item, stockKeys.weekHigh52, firstDefined(metrics, stockKeys.weekHigh52))),
    weekLow52: numeric(firstDefined(item, stockKeys.weekLow52, firstDefined(metrics, stockKeys.weekLow52))),
    about:
      item.about ||
      item.description ||
      item.company_profile ||
      metrics.about ||
      'Company overview is not available from the API yet.',
    keyPoints: toArray(item.key_points || item.keyPoints || metrics.key_points || metrics.keyPoints),
    pros: toArray(item.pros || metrics.pros),
    cons: toArray(item.cons || metrics.cons),
  };
}

export function normalizeStocksResponse(payload) {
  return toArray(payload?.stocks || payload?.results || payload).map(normalizeStock);
}

export function normalizeMarketResponse(payload) {
  const records = toArray(payload?.items || payload?.indices || payload?.market || payload);
  const items = records.map((item) => ({
    name: stringValue(item.name || item.index || item.symbol, 'Index'),
    symbol: stringValue(item.symbol || item.ticker || item.name, 'IDX'),
    value: numeric(item.value ?? item.price ?? item.current ?? item.close),
    changePct: numeric(item.change_pct ?? item.changePercent ?? item.pct_change),
    change: numeric(item.change ?? item.delta),
    high: numeric(item.high),
    low: numeric(item.low),
    open: numeric(item.open),
    prevClose: numeric(item.prev_close ?? item.prevClose),
    timestamp: item.timestamp || item.updated_at || item.updatedAt || null,
    lastUpdated: item.last_updated || item.lastUpdated || item.timestamp || null,
    source: stringValue(item.source, 'Fallback'),
    isLive: Boolean(item.is_live ?? item.isLive ?? false),
  }));

  return {
    items,
    meta: {
      source: stringValue(payload?.meta?.source, items.some((item) => item.source === 'Angel One') ? 'Angel One' : 'Fallback'),
      isLive: Boolean(payload?.meta?.is_live ?? payload?.meta?.isLive ?? items.some((item) => item.isLive)),
      status: stringValue(payload?.meta?.status, 'ready'),
      message: stringValue(payload?.meta?.message, ''),
      lastUpdated: payload?.meta?.last_updated || payload?.meta?.lastUpdated || items.find((item) => item.lastUpdated)?.lastUpdated || null,
      revision: numeric(payload?.meta?.revision, 0),
    },
  };
}

function normalizeHistoryPoint(item = {}) {
  return {
    date: item.date || item.datetime || item.timestamp || item.Date,
    open: numeric(item.open ?? item.Open),
    high: numeric(item.high ?? item.High),
    low: numeric(item.low ?? item.Low),
    close: numeric(item.close ?? item.Close ?? item.price),
    volume: numeric(item.volume ?? item.Volume),
    sma50: numeric(item.sma_50 ?? item.SMA_50),
    sma200: numeric(item.sma_200 ?? item.SMA_200),
    rsi: numeric(item.rsi ?? item.RSI),
    macd: numeric(item.macd ?? item.MACD),
    signal: numeric(item.signal ?? item.Signal),
    bbUpper: numeric(item.bb_upper ?? item.BB_upper),
    bbLower: numeric(item.bb_lower ?? item.BB_lower),
    atr: numeric(item.atr ?? item.ATR),
    momentum: numeric(item.momentum ?? item.Momentum),
    volumeChange: numeric(item.volume_change ?? item.Volume_change),
  };
}

function normalizeNewsItem(item = {}) {
  return {
    id: item.id || item.url || item.title,
    title: item.title || item.headline || 'Untitled story',
    source: item.source || item.publisher || 'Unknown source',
    url: item.url || '#',
    publishedAt: item.published_at || item.publishedAt || item.date,
    sentiment: numeric(item.sentiment ?? item.sentiment_score ?? item.score),
    label: stringValue(item.label || item.sentiment_label, ''),
  };
}

function normalizeFeatureImportance(payload) {
  const entries = Array.isArray(payload)
    ? payload
    : Object.entries(payload || {}).map(([feature, value]) => ({ feature, value }));

  return entries
    .map((item) => ({
      feature: item.feature || item.name || item.label,
      value: numeric(item.value ?? item.importance ?? item.score),
    }))
    .filter((item) => item.feature)
    .sort((a, b) => b.value - a.value)
    .slice(0, 10);
}

function normalizeTable(payload) {
  return toArray(payload).map((row, index) => ({
    id: row.id || row.period || row.year || row.quarter || index,
    ...row,
  }));
}

function deriveHighlights(stock) {
  const pros = [];
  const cons = [];

  if (stock.rsi && stock.rsi < 55) pros.push('RSI remains below overheated levels.');
  if (stock.sentimentScore > 0.1) pros.push('News sentiment is supportive.');
  if (stock.changePct > 0) pros.push('Price action is positive on the latest session.');

  if (stock.rsi > 70) cons.push('RSI indicates overbought conditions.');
  if (stock.sentimentScore < -0.1) cons.push('Recent headlines lean negative.');
  if (stock.changePct < 0) cons.push('Latest session closed in the red.');

  return {
    pros: stock.pros.length ? stock.pros : pros,
    cons: stock.cons.length ? stock.cons : cons,
  };
}

export function normalizeStockDetailResponse(payload, symbol) {
  const company = normalizeStock({
    ...(payload?.stock || {}),
    ...(payload?.summary || {}),
    ...(payload || {}),
  });

  const merged = {
    ...company,
    symbol: company.symbol === '-' ? symbol : company.symbol,
    history: toArray(payload?.history || payload?.price_history || payload?.prices).map(normalizeHistoryPoint),
    news: toArray(payload?.news || payload?.headlines).map(normalizeNewsItem),
    featureImportance: normalizeFeatureImportance(
      payload?.feature_importance || payload?.featureImportance || payload?.model_features,
    ),
    modelUsed: stringValue(payload?.model_used || payload?.model || payload?.model_name, 'XGBoost / LightGBM'),
    quarters: normalizeTable(payload?.quarters || payload?.quarterly_results),
    profitLoss: normalizeTable(payload?.profit_and_loss || payload?.profitLoss),
    balanceSheet: normalizeTable(payload?.balance_sheet || payload?.balanceSheet),
    peers: normalizeTable(payload?.peers || payload?.peer_comparison).map(normalizeStock),
    sourceBreakdown: normalizeTable(payload?.source_breakdown || payload?.sources),
  };

  const derived = deriveHighlights(merged);

  return {
    ...merged,
    pros: derived.pros,
    cons: derived.cons,
  };
}

export function normalizeTopPicksResponse(payload) {
  return {
    buy: normalizeStocksResponse(payload?.buy || payload?.top_buy || payload?.topBuy || []),
    sell: normalizeStocksResponse(payload?.sell || payload?.top_sell || payload?.topSell || []),
  };
}
