/**
 * Tipos compartidos para datos de precios
 */

export interface PriceData {
  asset: string
  fiat: string
  buy_price: number
  sell_price: number
  market_buy: number
  market_sell: number
  spread: number
  margin: number
  timestamp: string
  trm?: number
}

export type Currency = 'COP' | 'VES' | 'USDT'

export type TradeDirection = 'buy' | 'sell'

export type PriceResponse = Record<string, PriceData>

export interface TradeStats {
  period_days: number
  total_trades: number
  completed: number
  pending: number
  failed: number
  automated_trades: number
  manual_trades: number
  total_profit: number
  total_volume_usd: number
  average_profit_per_trade: number
  success_rate: number
  only_real_trades?: boolean
  trade_breakdown?: {
    real_trades_count: number
    simulated_trades_count: number
    real_profit: number
    simulated_profit: number
    real_volume: number
    simulated_volume: number
  }
  by_currency?: Record<string, { count: number; volume: number; profit: number }>
}

export interface TrmResponse {
  current: number
  currency: string
  last_updated: string
  change_percentage: number
  history: Array<{ date: string; value: number }>
}

