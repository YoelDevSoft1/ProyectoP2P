'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Activity } from 'lucide-react'

interface ForexPair {
  id: string
  name: string
  price: number
  change24h: number
  changePercent: number
  high24h: number
  low24h: number
  volume24h: number
}

const FOREX_PAIRS_DATA: Omit<ForexPair, 'price' | 'change24h' | 'changePercent' | 'high24h' | 'low24h' | 'volume24h'>[] = [
  { id: 'EUR/USD', name: 'EUR/USD' },
  { id: 'GBP/USD', name: 'GBP/USD' },
  { id: 'USD/JPY', name: 'USD/JPY' },
  { id: 'AUD/USD', name: 'AUD/USD' },
  { id: 'USD/CAD', name: 'USD/CAD' },
  { id: 'USD/CHF', name: 'USD/CHF' },
  { id: 'NZD/USD', name: 'NZD/USD' },
  { id: 'EUR/GBP', name: 'EUR/GBP' },
  { id: 'EUR/JPY', name: 'EUR/JPY' },
  { id: 'GBP/JPY', name: 'GBP/JPY' },
]

interface ForexPairsListProps {
  onPairSelect?: (pair: string) => void
  selectedPair?: string
}

export function ForexPairsList({ onPairSelect, selectedPair }: ForexPairsListProps) {
  const [pairs, setPairs] = useState<ForexPair[]>([])
  const [sortBy, setSortBy] = useState<'name' | 'price' | 'change'>('name')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')

  // Precios base por par
  const basePrices: Record<string, number> = {
    'EUR/USD': 1.0850,
    'GBP/USD': 1.2750,
    'USD/JPY': 145.50,
    'AUD/USD': 0.6550,
    'USD/CAD': 1.3550,
    'USD/CHF': 0.8850,
    'NZD/USD': 0.6050,
    'EUR/GBP': 0.8510,
    'EUR/JPY': 157.85,
    'GBP/JPY': 185.51,
  }

  useEffect(() => {
    // Inicializar pares con datos simulados
    const initialPairs: ForexPair[] = FOREX_PAIRS_DATA.map((pair) => {
      const basePrice = basePrices[pair.id] || 1.0
      const changePercent = (Math.random() - 0.5) * 2 // -1% a +1%
      const change24h = basePrice * (changePercent / 100)
      const high24h = basePrice * (1 + Math.abs(changePercent) / 100 + Math.random() * 0.005)
      const low24h = basePrice * (1 - Math.abs(changePercent) / 100 - Math.random() * 0.005)
      const volume24h = Math.random() * 50000000000 + 10000000000

      return {
        ...pair,
        price: basePrice,
        change24h,
        changePercent,
        high24h,
        low24h,
        volume24h,
      }
    })

    setPairs(initialPairs)

    // Actualizar precios en tiempo real
    const interval = setInterval(() => {
      setPairs((prev) =>
        prev.map((pair) => {
          const basePrice = basePrices[pair.id] || pair.price
          const volatility = basePrice * 0.0001 // 0.01% de volatilidad
          const change = (Math.random() - 0.5) * volatility * 2
          const newPrice = pair.price + change
          const change24h = newPrice - basePrice
          const changePercent = (change24h / basePrice) * 100
          const high24h = Math.max(pair.high24h, newPrice)
          const low24h = Math.min(pair.low24h, newPrice)

          return {
            ...pair,
            price: newPrice,
            change24h,
            changePercent,
            high24h,
            low24h,
          }
        })
      )
    }, 2000) // Actualizar cada 2 segundos

    return () => clearInterval(interval)
  }, [])

  const sortedPairs = [...pairs].sort((a, b) => {
    let comparison = 0
    switch (sortBy) {
      case 'name':
        comparison = a.name.localeCompare(b.name)
        break
      case 'price':
        comparison = a.price - b.price
        break
      case 'change':
        comparison = a.changePercent - b.changePercent
        break
    }
    return sortOrder === 'asc' ? comparison : -comparison
  })

  const handleSort = (column: 'name' | 'price' | 'change') => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('asc')
    }
  }

  const formatPrice = (price: number, pair: string) => {
    const decimals = pair.includes('JPY') ? 2 : 5
    return price.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
  }

  const formatVolume = (volume: number) => {
    if (volume >= 1e9) return `$${(volume / 1e9).toFixed(2)}B`
    if (volume >= 1e6) return `$${(volume / 1e6).toFixed(2)}M`
    return `$${(volume / 1e3).toFixed(2)}K`
  }

  const SortIcon = ({ column }: { column: 'name' | 'price' | 'change' }) => {
    if (sortBy !== column) return null
    return sortOrder === 'asc' ? (
      <TrendingUp className="h-3 w-3 ml-1" />
    ) : (
      <TrendingDown className="h-3 w-3 ml-1" />
    )
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl overflow-hidden">
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary-400" />
            Pares Forex
          </h3>
          <span className="text-sm text-gray-400">{pairs.length} pares</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-800/50 border-b border-gray-700">
            <tr>
              <th
                className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-300 transition"
                onClick={() => handleSort('name')}
              >
                <div className="flex items-center">
                  Par
                  <SortIcon column="name" />
                </div>
              </th>
              <th
                className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-300 transition"
                onClick={() => handleSort('price')}
              >
                <div className="flex items-center justify-end">
                  Precio
                  <SortIcon column="price" />
                </div>
              </th>
              <th
                className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-300 transition"
                onClick={() => handleSort('change')}
              >
                <div className="flex items-center justify-end">
                  24h
                  <SortIcon column="change" />
                </div>
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Alto 24h
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Bajo 24h
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Volumen 24h
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {sortedPairs.map((pair) => (
              <tr
                key={pair.id}
                onClick={() => onPairSelect?.(pair.id)}
                className={`cursor-pointer transition hover:bg-gray-800/50 ${
                  selectedPair === pair.id ? 'bg-primary-500/10 border-l-2 border-primary-500' : ''
                }`}
              >
                <td className="px-4 py-3">
                  <span className="text-white font-semibold">{pair.name}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-white font-medium">{formatPrice(pair.price, pair.id)}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span
                    className={`font-semibold flex items-center justify-end gap-1 ${
                      pair.changePercent >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}
                  >
                    {pair.changePercent >= 0 ? (
                      <TrendingUp className="h-3 w-3" />
                    ) : (
                      <TrendingDown className="h-3 w-3" />
                    )}
                    {pair.changePercent >= 0 ? '+' : ''}
                    {pair.changePercent.toFixed(2)}%
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-gray-300">{formatPrice(pair.high24h, pair.id)}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-gray-300">{formatPrice(pair.low24h, pair.id)}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-gray-400">{formatVolume(pair.volume24h)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

