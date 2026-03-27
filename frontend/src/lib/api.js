import {
  normalizeMarketResponse,
  normalizeStockDetailResponse,
  normalizeStocksResponse,
  normalizeTopPicksResponse,
} from './normalize';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function getMarketSocketUrl() {
  const baseUrl = API_BASE_URL.replace(/^http/, 'ws');
  return `${baseUrl}/ws/market`;
}

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
}

export const api = {
  async getBootstrap() {
    const data = await request('/api/bootstrap');
    return {
      market: normalizeMarketResponse(data?.market || []),
      stocks: normalizeStocksResponse(data?.stocks || []),
    };
  },
  async getStocks() {
    const data = await request('/api/stocks');
    return normalizeStocksResponse(data);
  },
  async getStock(symbol) {
    const data = await request(`/api/stocks/${symbol}`);
    return normalizeStockDetailResponse(data, symbol);
  },
  async getMarket() {
    const data = await request('/api/market');
    return normalizeMarketResponse(data);
  },
  async getTopPicks() {
    const data = await request('/api/top-picks');
    return normalizeTopPicksResponse(data);
  },
};
