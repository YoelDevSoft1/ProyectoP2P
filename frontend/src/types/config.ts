/**
 * Tipos TypeScript para la API de Configuración
 */

export type TradingMode = 'manual' | 'auto' | 'hybrid'

export interface TradingConfig {
  trading_mode: TradingMode
  profit_margin_cop: number  // 0-10 (%)
  profit_margin_ves: number  // 0-10 (%)
  min_trade_amount: number   // >= 0 (USD)
  max_trade_amount: number   // >= 0 (USD)
  max_daily_trades: number   // 1-1000
  stop_loss_percentage: number // 0-10 (%)
}

export interface P2PConfig {
  monitored_assets: string[]  // ej: ["USDT", "BTC"]
  monitored_fiats: string[]   // ej: ["COP", "VES"]
  analysis_rows: number       // 1-100
  top_spreads: number         // 1-20
  price_cache_seconds: number // 1-3600
  min_surplus_usdt: number    // >= 0
}

export interface ArbitrageConfig {
  monitored_assets: string[]
  monitored_fiats: string[]
  top_opportunities: number     // 1-50
  min_liquidity_usdt: number    // >= 0
  min_profit: number            // >= 0 (%)
  update_price_interval: number // 1-3600 (segundos)
}

export interface NotificationConfig {
  enable_notifications: boolean
  telegram_bot_token: string | null  // Oculto: solo se muestra "12345678..."
  telegram_chat_id: string | null
  email_smtp_server: string | null
  email_smtp_port: number            // 1-65535
  email_from: string | null
}

export interface MLConfig {
  retrain_interval: number      // >= 3600 (segundos)
  min_data_points: number       // >= 100
  confidence_threshold: number  // 0-1
  spread_threshold: number      // 0-10 (%)
}

export interface AlphaVantageConfig {
  api_key: string | null  // Oculto: solo se muestra "A828MZ96..."
  enabled: boolean
  cache_ttl: number       // 60-3600 (segundos)
}

export interface FXConfig {
  cache_ttl_seconds: number    // 60-3600
  trm_update_interval: number  // 60-3600
  ves_update_interval: number  // 60-3600
  fallback_rates: {
    [key: string]: number  // ej: { "COP": 4000.0, "VES": 36.5 }
  }
}

export interface RateLimitConfig {
  rate_limit_per_minute: number     // 1-1000
  rate_limit_binance_api: number    // 1-10000
}

export interface BrowserConfig {
  headless: boolean
  timeout: number        // 1000-300000 (ms)
  pool_size: number      // 1-10
}

export interface AppConfigResponse {
  trading: TradingConfig
  p2p: P2PConfig
  arbitrage: ArbitrageConfig
  notifications: NotificationConfig
  ml: MLConfig
  alpha_vantage: AlphaVantageConfig
  fx: FXConfig
  rate_limiting: RateLimitConfig
  browser: BrowserConfig
  environment: string    // "development" | "staging" | "production"
  version: string
  debug: boolean
}

export interface ConfigUpdateRequest {
  trading?: Partial<TradingConfig>
  p2p?: Partial<P2PConfig>
  arbitrage?: Partial<ArbitrageConfig>
  notifications?: Partial<NotificationConfig>
  ml?: Partial<MLConfig>
  alpha_vantage?: Partial<AlphaVantageConfig>
  fx?: Partial<FXConfig>
  rate_limiting?: Partial<RateLimitConfig>
  browser?: Partial<BrowserConfig>
}

export interface ConfigSection {
  id: string
  name: string
  description: string
  icon: string
  fields: string[]
}

export interface ConfigSectionsResponse {
  sections: ConfigSection[]
}

