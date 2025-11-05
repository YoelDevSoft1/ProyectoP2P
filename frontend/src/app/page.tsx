import LandingPage from '@/components/LandingPage'
import { StructuredData } from '@/components/StructuredData'

type PriceResponse = Record<string, any>

type TradeStats = {
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
  by_currency?: Record<string, { count: number; volume: number; profit: number }>
}

type TrmResponse = {
  current: number
  currency: string
  last_updated: string
  change_percentage: number
  history: Array<{ date: string; value: number }>
}

const apiBase =
  process.env.NEXT_INTERNAL_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000'

async function fetchJson<T>(endpoint: string): Promise<T | null> {
  const url = `${apiBase.replace(/\/$/, '')}${endpoint}`

  try {
    const res = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        // Header para evitar la página de interceptor de ngrok
        'ngrok-skip-browser-warning': 'true',
      },
      // No cache to keep data fresh for landing conversions
      cache: 'no-store',
    })

    if (!res.ok) {
      console.error(`Error fetching ${endpoint}:`, res.statusText)
      return null
    }

    return (await res.json()) as T
  } catch (error) {
    console.error(`Request failed for ${endpoint}:`, error)
    return null
  }
}

export default async function Page() {
  const [initialPrices, initialTrm, initialStats] = await Promise.all([
    fetchJson<PriceResponse>('/api/v1/prices/current?asset=USDT'),
    fetchJson<TrmResponse>('/api/v1/prices/trm'),
    fetchJson<TradeStats>('/api/v1/trades/stats/summary?days=7'),
  ])

  return (
    <>
      <LandingPage
        initialPrices={initialPrices}
        initialTrm={initialTrm}
        initialStats={initialStats}
      />
      <StructuredData prices={initialPrices} stats={initialStats} trm={initialTrm} />
    </>
  )
}
