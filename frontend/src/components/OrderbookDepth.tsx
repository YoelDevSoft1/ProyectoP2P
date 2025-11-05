'use client'

import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import { TrendingUp, TrendingDown, Activity } from 'lucide-react'

interface OrderbookDepthProps {
  asset?: string
  fiat?: string
}

interface DepthData {
  success: boolean
  spread: {
    best_bid: number
    best_ask: number
    percentage: number
  }
  bids: {
    total_volume: number
    orders: Array<{ price: number; quantity: number }>
  }
  asks: {
    total_volume: number
    orders: Array<{ price: number; quantity: number }>
  }
  imbalance: {
    ratio: number
    signal: string
  }
  liquidity_score: {
    score: number
    rating: string
  }
}

export function OrderbookDepth({ asset = 'USDT', fiat = 'COP' }: OrderbookDepthProps) {
  const [depthData, setDepthData] = useState<DepthData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDepthData()
    const interval = setInterval(fetchDepthData, 15000) // Refresh every 15s

    return () => clearInterval(interval)
  }, [asset, fiat])

  const fetchDepthData = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/liquidity/market-depth?asset=${asset}&fiat=${fiat}&depth_levels=10`,
        {
          headers: {
            'ngrok-skip-browser-warning': 'true',
          },
        }
      )
      const data = await response.json()

      if (data.success) {
        setDepthData(data)
      }
    } catch (error) {
      console.error('Error fetching depth data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-700 rounded"></div>
        </div>
      </div>
    )
  }

  if (!depthData || !depthData.success) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <p className="text-gray-400">No depth data available</p>
      </div>
    )
  }

  // Preparar datos para el gráfico
  const chartData = [
    // Bids (compras) - en rojo/verde según mercado
    ...depthData.bids.orders.slice(0, 10).reverse().map((order) => ({
      price: order.price,
      bidVolume: order.quantity,
      askVolume: 0,
      type: 'BID',
    })),
    // Asks (ventas)
    ...depthData.asks.orders.slice(0, 10).map((order) => ({
      price: order.price,
      bidVolume: 0,
      askVolume: order.quantity,
      type: 'ASK',
    })),
  ]

  const imbalanceColor =
    depthData.imbalance.signal === 'BULLISH' ? 'text-green-400' :
    depthData.imbalance.signal === 'BEARISH' ? 'text-red-400' : 'text-gray-400'

  const scoreColor =
    depthData.liquidity_score.score >= 80 ? 'text-green-400' :
    depthData.liquidity_score.score >= 60 ? 'text-yellow-400' :
    depthData.liquidity_score.score >= 40 ? 'text-orange-400' : 'text-red-400'

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Activity className="h-6 w-6 text-primary-400" />
          <div>
            <h3 className="text-xl font-bold text-white">
              Profundidad de Mercado
            </h3>
            <p className="text-sm text-gray-400">
              {asset}/{fiat} Orderbook Depth
            </p>
          </div>
        </div>

        {/* Liquidity Score */}
        <div className="text-right">
          <p className="text-sm text-gray-400">Liquidity Score</p>
          <p className={`text-2xl font-bold ${scoreColor}`}>
            {depthData.liquidity_score.score.toFixed(0)}
            <span className="text-sm ml-1">{depthData.liquidity_score.rating}</span>
          </p>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Spread */}
        <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Spread</span>
            <TrendingUp className="h-4 w-4 text-yellow-400" />
          </div>
          <p className="text-2xl font-bold text-white">
            {depthData.spread.percentage.toFixed(2)}%
          </p>
          <div className="mt-2 flex justify-between text-xs">
            <span className="text-green-400">
              Bid: {depthData.spread.best_bid.toLocaleString()}
            </span>
            <span className="text-red-400">
              Ask: {depthData.spread.best_ask.toLocaleString()}
            </span>
          </div>
        </div>

        {/* Order Imbalance */}
        <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Order Imbalance</span>
            {depthData.imbalance.signal === 'BULLISH' ? (
              <TrendingUp className="h-4 w-4 text-green-400" />
            ) : depthData.imbalance.signal === 'BEARISH' ? (
              <TrendingDown className="h-4 w-4 text-red-400" />
            ) : (
              <Activity className="h-4 w-4 text-gray-400" />
            )}
          </div>
          <p className={`text-2xl font-bold ${imbalanceColor}`}>
            {(depthData.imbalance.ratio * 100).toFixed(1)}%
          </p>
          <p className="mt-2 text-xs text-gray-400">
            {depthData.imbalance.signal}
          </p>
        </div>

        {/* Total Volume */}
        <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Total Liquidity</span>
            <Activity className="h-4 w-4 text-blue-400" />
          </div>
          <p className="text-2xl font-bold text-white">
            {(depthData.bids.total_volume + depthData.asks.total_volume).toLocaleString(undefined, {
              maximumFractionDigits: 0
            })}
          </p>
          <div className="mt-2 flex justify-between text-xs">
            <span className="text-green-400">
              Bids: {depthData.bids.total_volume.toFixed(0)}
            </span>
            <span className="text-red-400">
              Asks: {depthData.asks.total_volume.toFixed(0)}
            </span>
          </div>
        </div>
      </div>

      {/* Orderbook Depth Chart */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="price"
              stroke="#9CA3AF"
              tick={{ fill: '#9CA3AF', fontSize: 12 }}
              tickFormatter={(value) => value.toLocaleString()}
            />
            <YAxis
              stroke="#9CA3AF"
              tick={{ fill: '#9CA3AF', fontSize: 12 }}
              label={{ value: 'Volume', angle: -90, position: 'insideLeft', fill: '#9CA3AF' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#fff',
              }}
              labelStyle={{ color: '#9CA3AF' }}
              formatter={(value: number, name: string) => [
                value.toFixed(2),
                name === 'bidVolume' ? 'Bid Volume' : 'Ask Volume',
              ]}
            />
            <Legend
              wrapperStyle={{ color: '#9CA3AF' }}
              formatter={(value) => (value === 'bidVolume' ? 'Bids (Compra)' : 'Asks (Venta)')}
            />
            <Bar dataKey="bidVolume" stackId="a">
              {chartData.map((entry, index) => (
                <Cell key={`cell-bid-${index}`} fill={entry.type === 'BID' ? '#10B981' : 'transparent'} />
              ))}
            </Bar>
            <Bar dataKey="askVolume" stackId="a">
              {chartData.map((entry, index) => (
                <Cell key={`cell-ask-${index}`} fill={entry.type === 'ASK' ? '#EF4444' : 'transparent'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Footer note */}
      <div className="mt-4 text-xs text-gray-500 text-center">
        Actualizado cada 15 segundos • Showing top 10 niveles por lado
      </div>
    </div>
  )
}
