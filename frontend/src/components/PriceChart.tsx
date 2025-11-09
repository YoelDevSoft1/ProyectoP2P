'use client'

import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { TrendingUp, TrendingDown, Clock } from 'lucide-react'
import { useState } from 'react'
import api from '@/lib/api'

interface PriceChartProps {
  currency: 'COP' | 'VES'
  initialData?: Array<{ date: string; value: number }>
}

type Timeframe = '24h' | '7d' | '30d'

export function PriceChart({ currency, initialData }: PriceChartProps) {
  const [timeframe, setTimeframe] = useState<Timeframe>('24h')
  const [priceType, setPriceType] = useState<'buy' | 'sell'>('sell')

  const hoursMap: Record<Timeframe, number> = {
    '24h': 24,
    '7d': 168,
    '30d': 720,
  }

  const { data: historyData, isLoading } = useQuery({
    queryKey: ['price-history', currency, timeframe, priceType],
    queryFn: () => api.getPriceHistory('USDT', currency, hoursMap[timeframe]),
    refetchInterval: 60000, // Actualizar cada minuto
    enabled: true,
  })

  // Procesar datos para el gráfico
  const rawData = historyData?.history || initialData || []
  const shouldShowTime = rawData.length < 50
  
  const chartData = rawData.map((item: any) => {
    const date = new Date(item.timestamp || item.date)
    // El backend devuelve bid (compra) y ask (venta)
    // bid = precio al que compramos (buy), ask = precio al que vendemos (sell)
    const buyPrice = item.bid || item.buy_price || item.avg || item.value || 0
    const sellPrice = item.ask || item.sell_price || item.avg || item.value || 0
    return {
      date: shouldShowTime
        ? date.toLocaleDateString('es', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
        : date.toLocaleDateString('es', { month: 'short', day: 'numeric' }),
      timestamp: date.getTime(),
      value: priceType === 'buy' ? buyPrice : sellPrice,
      buy_price: buyPrice,
      sell_price: sellPrice,
      spread: item.spread,
    }
  }).filter((item: any) => item.value > 0)

  // Calcular tendencia
  const trend = chartData.length >= 2
    ? chartData[chartData.length - 1].value > chartData[0].value
      ? 'up'
      : 'down'
    : 'neutral'

  const trendPercentage = chartData.length >= 2
    ? ((chartData[chartData.length - 1].value - chartData[0].value) / chartData[0].value) * 100
    : 0

  const currencySymbol = currency === 'COP' ? '$' : 'Bs.'
  const currencyName = currency === 'COP' ? 'Peso Colombiano' : 'Bolívar Venezolano'

  const formatValue = (value: number) => {
    if (currency === 'VES') {
      return value.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }
    return value.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-xl">
          <p className="text-sm text-gray-400 mb-2">{data.date}</p>
          <p className="text-lg font-bold text-white">
            {currencySymbol}{formatValue(data.value)} {currency}
          </p>
          {data.buy_price && data.sell_price && (
            <div className="mt-2 space-y-1 text-xs">
              <p className="text-green-400">
                Compra: {currencySymbol}{formatValue(data.buy_price)}
              </p>
              <p className="text-red-400">
                Venta: {currencySymbol}{formatValue(data.sell_price)}
              </p>
            </div>
          )}
        </div>
      )
    }
    return null
  }

  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700 shadow-xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white mb-1">
            Precio Histórico USDT/{currency}
          </h3>
          <p className="text-sm text-gray-400">{currencyName}</p>
        </div>
        <div className="flex items-center gap-2 mt-2 sm:mt-0">
          {trend !== 'neutral' && (
            <div
              className={`flex items-center gap-1 px-3 py-1 rounded-full ${
                trend === 'up'
                  ? 'bg-green-900/30 text-green-400 border border-green-700/50'
                  : 'bg-red-900/30 text-red-400 border border-red-700/50'
              }`}
            >
              {trend === 'up' ? (
                <TrendingUp className="h-4 w-4" />
              ) : (
                <TrendingDown className="h-4 w-4" />
              )}
              <span className="text-sm font-medium">
                {trendPercentage >= 0 ? '+' : ''}
                {trendPercentage.toFixed(2)}%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Controles */}
      <div className="flex flex-wrap gap-2 mb-4">
        <div className="flex gap-1 p-1 bg-gray-700/50 rounded-lg">
          {(['24h', '7d', '30d'] as Timeframe[]).map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-3 py-1 rounded-md text-sm font-medium transition-all ${
                timeframe === tf
                  ? 'bg-primary-600 text-white shadow-lg'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
        <div className="flex gap-1 p-1 bg-gray-700/50 rounded-lg">
          {(['buy', 'sell'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setPriceType(type)}
              className={`px-3 py-1 rounded-md text-sm font-medium transition-all ${
                priceType === type
                  ? 'bg-primary-600 text-white shadow-lg'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {type === 'buy' ? 'Compra' : 'Venta'}
            </button>
          ))}
        </div>
      </div>

      {/* Gráfico */}
      {isLoading && !chartData.length ? (
        <div className="h-64 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Cargando datos históricos...</p>
          </div>
        </div>
      ) : chartData.length === 0 ? (
        <div className="h-64 flex items-center justify-center">
          <div className="text-center">
            <Clock className="h-12 w-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No hay datos históricos disponibles</p>
          </div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="date"
              stroke="#9CA3AF"
              style={{ fontSize: '12px' }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis
              stroke="#9CA3AF"
              style={{ fontSize: '12px' }}
              tickFormatter={(value) => {
                if (currency === 'VES') {
                  return (value / 1000000).toFixed(1) + 'M'
                }
                return (value / 1000).toFixed(0) + 'K'
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="value"
              stroke={priceType === 'buy' ? '#22c55e' : '#ef4444'}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
              name={priceType === 'buy' ? 'Precio de Compra' : 'Precio de Venta'}
            />
          </LineChart>
        </ResponsiveContainer>
      )}

      {/* Información adicional */}
      {chartData.length > 0 && (
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-xs text-gray-400 mb-1">Mínimo</p>
            <p className="text-sm font-semibold text-white">
              {currencySymbol}
              {formatValue(Math.min(...chartData.map((d) => d.value)))}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-1">Máximo</p>
            <p className="text-sm font-semibold text-white">
              {currencySymbol}
              {formatValue(Math.max(...chartData.map((d) => d.value)))}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-1">Promedio</p>
            <p className="text-sm font-semibold text-white">
              {currencySymbol}
              {formatValue(
                chartData.reduce((acc, d) => acc + d.value, 0) / chartData.length
              )}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-1">Actual</p>
            <p className="text-sm font-semibold text-white">
              {currencySymbol}
              {formatValue(chartData[chartData.length - 1]?.value || 0)}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

