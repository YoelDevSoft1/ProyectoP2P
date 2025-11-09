'use client'

import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, BarChart, Bar } from 'recharts'
import { TrendingUp, DollarSign, Activity } from 'lucide-react'
import api from '@/lib/api'
import { useState } from 'react'

export function PerformanceCharts() {
  const [timeframe, setTimeframe] = useState<'7d' | '30d' | '90d'>('30d')
  
  const daysMap = {
    '7d': 7,
    '30d': 30,
    '90d': 90,
  }

  const { data: stats } = useQuery({
    queryKey: ['performance-charts', timeframe],
    queryFn: () => api.getPerformanceMetrics(daysMap[timeframe]),
    refetchInterval: 60000,
  })

  // Obtener trades para calcular volumen y cantidad de trades
  const { data: tradesData } = useQuery({
    queryKey: ['trades-for-performance', timeframe],
    queryFn: async () => {
      try {
        const data = await api.getTrades(0, 1000, 'COMPLETED')
        return data
      } catch (error) {
        console.error('Error fetching trades:', error)
        return { trades: [], total: 0 }
      }
    },
    refetchInterval: 60000,
  })

  // Procesar datos del backend - SOLO datos reales
  const processChartData = () => {
    // Si hay datos del backend, procesarlos
    if (stats?.daily_profit && typeof stats.daily_profit === 'object') {
      const dailyProfit = stats.daily_profit as Record<string, number>
      const trades = tradesData?.trades || []
      const data: any[] = []
      let cumulativeProfit = 0
      
      // Agrupar trades por fecha
      const tradesByDate: Record<string, { volume: number; count: number }> = {}
      trades.forEach((trade: any) => {
        if (trade.status === 'COMPLETED' && trade.created_at) {
          const date = new Date(trade.created_at).toISOString().split('T')[0]
          if (!tradesByDate[date]) {
            tradesByDate[date] = { volume: 0, count: 0 }
          }
          tradesByDate[date].volume += trade.crypto_amount || 0
          tradesByDate[date].count += 1
        }
      })
      
      // Convertir objeto a array y ordenar por fecha
      const sortedEntries = Object.entries(dailyProfit).sort((a, b) => 
        new Date(a[0]).getTime() - new Date(b[0]).getTime()
      )
      
      sortedEntries.forEach(([dateStr, profit]) => {
        const date = new Date(dateStr)
        cumulativeProfit += profit
        const dateData = tradesByDate[dateStr] || { volume: 0, count: 0 }
        
        data.push({
          date: date.toLocaleDateString('es', { month: 'short', day: 'numeric' }),
          profit: profit,
          volume: dateData.volume,
          trades: dateData.count,
          cumulativeProfit: cumulativeProfit,
        })
      })
      
      return data
    }
    
    // Si no hay datos, retornar array vacío
    return []
  }

  const chartData = processChartData()

  // Calcular métricas de tendencia
  const profitTrend = chartData.length >= 2
    ? chartData[chartData.length - 1].profit > chartData[0].profit
      ? 'up'
      : 'down'
    : 'neutral'

  const totalProfit = chartData.reduce((acc: number, d: any) => acc + (d.profit || 0), 0)
  const totalVolume = chartData.reduce((acc: number, d: any) => acc + (d.volume || 0), 0)
  const totalTrades = chartData.reduce((acc: number, d: any) => acc + (d.trades || 0), 0)

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-xl">
          <p className="text-sm text-gray-400 mb-2">{payload[0].payload.date}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm font-medium" style={{ color: entry.color }}>
              {entry.name}: {entry.name.includes('Profit') ? '$' : entry.name.includes('Volume') ? '$' : ''}
              {entry.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  // Si no hay datos, mostrar estado vacío
  if (chartData.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-white">Análisis de Rendimiento</h2>
        </div>
        <div className="bg-gray-800 rounded-xl p-12 border border-gray-700 text-center">
          <Activity className="h-12 w-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg mb-2">No hay datos de rendimiento disponibles</p>
          <p className="text-gray-500 text-sm">Los datos aparecerán aquí una vez que haya trades completados</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Análisis de Rendimiento</h2>
        <div className="flex gap-2">
          {(['7d', '30d', '90d'] as const).map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                timeframe === tf
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      {/* Métricas Resumen */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-green-900/30 to-green-800/20 border border-green-700/50 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Ganancia Total</span>
            <DollarSign className="h-5 w-5 text-green-400" />
          </div>
          <p className="text-3xl font-bold text-white">${totalProfit.toFixed(2)}</p>
          <div className="flex items-center gap-2 mt-2">
            {profitTrend === 'up' ? (
              <TrendingUp className="h-4 w-4 text-green-400" />
            ) : profitTrend === 'down' ? (
              <TrendingUp className="h-4 w-4 text-red-400 rotate-180" />
            ) : null}
            <span className="text-sm text-gray-400">
              {profitTrend === 'up' ? 'Tendencia alcista' : profitTrend === 'down' ? 'Tendencia bajista' : 'Estable'}
            </span>
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border border-blue-700/50 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Volumen Total</span>
            <Activity className="h-5 w-5 text-blue-400" />
          </div>
          <p className="text-3xl font-bold text-white">${totalVolume.toLocaleString('en-US', { minimumFractionDigits: 0 })}</p>
          <p className="text-sm text-gray-400 mt-2">Promedio: ${(totalVolume / chartData.length).toLocaleString('en-US', { minimumFractionDigits: 0 })}/día</p>
        </div>

        <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/20 border border-purple-700/50 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Operaciones Totales</span>
            <Activity className="h-5 w-5 text-purple-400" />
          </div>
          <p className="text-3xl font-bold text-white">{totalTrades}</p>
          <p className="text-sm text-gray-400 mt-2">Promedio: {(totalTrades / chartData.length).toFixed(1)}/día</p>
        </div>
      </div>

      {/* Gráfico de Ganancia Acumulada */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
        <h3 className="text-lg font-bold text-white mb-4">Ganancia Acumulada</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="date" stroke="#9CA3AF" style={{ fontSize: '12px' }} />
            <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} tickFormatter={(value) => `$${value.toFixed(0)}`} />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="cumulativeProfit"
              stroke="#22c55e"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorProfit)"
              name="Ganancia Acumulada"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Gráfico de Ganancia Diaria y Volumen */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">Ganancia Diaria</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9CA3AF" style={{ fontSize: '12px' }} />
              <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} tickFormatter={(value) => `$${value.toFixed(0)}`} />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="profit"
                stroke="#22c55e"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6 }}
                name="Ganancia Diaria"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">Volumen Diario</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9CA3AF" style={{ fontSize: '12px' }} />
              <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} tickFormatter={(value) => `$${value / 1000}k`} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="volume" fill="#3b82f6" name="Volumen" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Gráfico de Operaciones Diarias */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
        <h3 className="text-lg font-bold text-white mb-4">Operaciones Diarias</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="date" stroke="#9CA3AF" style={{ fontSize: '12px' }} />
            <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="trades" fill="#a855f7" name="Operaciones" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

