'use client'

import { TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight } from 'lucide-react'
import { useState, useEffect } from 'react'
import { PriceData } from '@/types/prices'
import { formatColombiaTimeOnly } from '@/lib/dateUtils'

interface PriceCardProps {
  currency: 'COP' | 'VES'
  data: PriceData
  trm?: number
}

const CURRENCY_INFO = {
  COP: {
    name: 'Peso Colombiano',
    flag: '🇨🇴',
    symbol: '$',
  },
  VES: {
    name: 'Bolívar Venezolano',
    flag: '🇻🇪',
    symbol: 'Bs.',
  },
}

export function PriceCard({ currency, data, trm }: PriceCardProps) {
  const info = CURRENCY_INFO[currency]
  const [previousBuyPrice, setPreviousBuyPrice] = useState(data.buy_price)
  const [previousSellPrice, setPreviousSellPrice] = useState(data.sell_price)
  const [buyPriceChange, setBuyPriceChange] = useState<'up' | 'down' | null>(null)
  const [sellPriceChange, setSellPriceChange] = useState<'up' | 'down' | null>(null)

  // Detectar cambios de precio
  useEffect(() => {
    if (data.buy_price !== previousBuyPrice) {
      setBuyPriceChange(data.buy_price > previousBuyPrice ? 'up' : 'down')
      setPreviousBuyPrice(data.buy_price)
      setTimeout(() => setBuyPriceChange(null), 2000)
    }
  }, [data.buy_price, previousBuyPrice])

  useEffect(() => {
    if (data.sell_price !== previousSellPrice) {
      setSellPriceChange(data.sell_price > previousSellPrice ? 'up' : 'down')
      setPreviousSellPrice(data.sell_price)
      setTimeout(() => setSellPriceChange(null), 2000)
    }
  }, [data.sell_price, previousSellPrice])

  const formatCurrency = (value: number) => {
    if (currency === 'VES') {
      return value.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }
    return value.toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }

  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-8 border border-gray-700 shadow-xl hover:shadow-2xl transition-shadow">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <span className="text-4xl">{info.flag}</span>
          <div>
            <h3 className="text-2xl font-bold text-white">USDT / {currency}</h3>
            <p className="text-sm text-gray-400">{info.name}</p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-xs text-gray-500">Margen</span>
          <p className="text-lg font-semibold text-primary-500">+{data.margin}%</p>
        </div>
      </div>

      {/* Prices */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div 
          className={`bg-green-900/20 border border-green-700 rounded-lg p-4 transition-all duration-300 ${
            buyPriceChange === 'up' ? 'ring-2 ring-green-400 scale-105' : 
            buyPriceChange === 'down' ? 'ring-2 ring-green-600 scale-105' : ''
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Nosotros compramos</span>
            <div className="flex items-center gap-1">
              {buyPriceChange === 'up' && <ArrowUpRight className="h-4 w-4 text-green-400 animate-pulse" />}
              {buyPriceChange === 'down' && <ArrowDownRight className="h-4 w-4 text-green-600 animate-pulse" />}
              {!buyPriceChange && <TrendingDown className="h-4 w-4 text-green-500" />}
            </div>
          </div>
          <p className={`text-2xl font-bold text-green-500 transition-all ${
            buyPriceChange ? 'scale-110' : ''
          }`}>
            {info.symbol}{formatCurrency(data.buy_price)}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Mercado: {info.symbol}{formatCurrency(data.market_sell)}
          </p>
        </div>

        <div 
          className={`bg-red-900/20 border border-red-700 rounded-lg p-4 transition-all duration-300 ${
            sellPriceChange === 'up' ? 'ring-2 ring-red-400 scale-105' : 
            sellPriceChange === 'down' ? 'ring-2 ring-red-600 scale-105' : ''
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Nosotros vendemos</span>
            <div className="flex items-center gap-1">
              {sellPriceChange === 'up' && <ArrowUpRight className="h-4 w-4 text-red-400 animate-pulse" />}
              {sellPriceChange === 'down' && <ArrowDownRight className="h-4 w-4 text-red-600 animate-pulse" />}
              {!sellPriceChange && <TrendingUp className="h-4 w-4 text-red-500" />}
            </div>
          </div>
          <p className={`text-2xl font-bold text-red-500 transition-all ${
            sellPriceChange ? 'scale-110' : ''
          }`}>
            {info.symbol}{formatCurrency(data.sell_price)}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Mercado: {info.symbol}{formatCurrency(data.market_buy)}
          </p>
        </div>
      </div>

      {/* Spread Info */}
      <div className="bg-gray-700/30 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">Spread</span>
          <span className="text-lg font-semibold text-primary-400">
            {data.spread.toFixed(2)}%
          </span>
        </div>
        {currency === 'COP' && trm && (
          <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-600">
            <span className="text-sm text-gray-400">TRM</span>
            <span className="text-sm font-medium text-gray-300">
              ${trm.toLocaleString('es-CO', { minimumFractionDigits: 2 })}
            </span>
          </div>
        )}
      </div>

      {/* Last Update */}
      <div className="mt-4 text-center">
        <p className="text-xs text-gray-500">
          Actualizado: {formatColombiaTimeOnly(data.timestamp)}
        </p>
      </div>
    </div>
  )
}
