'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface OrderBookEntry {
  price: number
  amount: number
  total: number
}

interface ForexOrderBookProps {
  pair: string
  currentPrice: number
}

export function ForexOrderBook({ pair, currentPrice }: ForexOrderBookProps) {
  const [bids, setBids] = useState<OrderBookEntry[]>([])
  const [asks, setAsks] = useState<OrderBookEntry[]>([])
  const [spread, setSpread] = useState<number>(0)
  const [spreadPercent, setSpreadPercent] = useState<number>(0)

  useEffect(() => {
    const generateOrderBook = () => {
      const pipValue = pair.includes('JPY') ? 0.01 : 0.0001
      const levels = 20
      const baseAmount = 100000

      const newBids: OrderBookEntry[] = []
      const newAsks: OrderBookEntry[] = []
      let bidTotal = 0
      let askTotal = 0

      // Generar bids (ofertas de compra)
      for (let i = 0; i < levels; i++) {
        const priceOffset = i * pipValue * 10
        const price = currentPrice - priceOffset
        const amount = baseAmount * (1 - i * 0.05) + Math.random() * baseAmount * 0.2
        bidTotal += amount

        newBids.push({
          price: Number(price.toFixed(5)),
          amount: Number(amount.toFixed(2)),
          total: Number(bidTotal.toFixed(2)),
        })
      }

      // Generar asks (ofertas de venta)
      for (let i = 0; i < levels; i++) {
        const priceOffset = i * pipValue * 10
        const price = currentPrice + priceOffset
        const amount = baseAmount * (1 - i * 0.05) + Math.random() * baseAmount * 0.2
        askTotal += amount

        newAsks.push({
          price: Number(price.toFixed(5)),
          amount: Number(amount.toFixed(2)),
          total: Number(askTotal.toFixed(2)),
        })
      }

      setBids(newBids.reverse()) // Mostrar más cercanos primero
      setAsks(newAsks)

      // Calcular spread
      if (newAsks.length > 0 && newBids.length > 0) {
        const bestAsk = newAsks[0].price
        const bestBid = newBids[newBids.length - 1].price
        const spreadValue = bestAsk - bestBid
        const spreadPct = (spreadValue / currentPrice) * 100
        setSpread(spreadValue)
        setSpreadPercent(spreadPct)
      }
    }

    generateOrderBook()

    // Actualizar cada segundo
    const interval = setInterval(() => {
      generateOrderBook()
    }, 1000)

    return () => clearInterval(interval)
  }, [pair, currentPrice])

  const formatPrice = (price: number) => {
    const decimals = pair.includes('JPY') ? 2 : 5
    return price.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
  }

  const formatAmount = (amount: number) => {
    if (amount >= 1000000) return `${(amount / 1000000).toFixed(2)}M`
    if (amount >= 1000) return `${(amount / 1000).toFixed(2)}K`
    return amount.toFixed(2)
  }

  const getMaxTotal = () => {
    const maxBid = Math.max(...bids.map((b) => b.total), 0)
    const maxAsk = Math.max(...asks.map((a) => a.total), 0)
    return Math.max(maxBid, maxAsk)
  }

  const maxTotal = getMaxTotal()

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl overflow-hidden">
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-white">Profundidad de Mercado</h3>
          <div className="flex items-center gap-4 text-sm">
            <div>
              <span className="text-gray-400">Spread: </span>
              <span className="text-red-400 font-semibold">{formatPrice(spread)}</span>
            </div>
            <div>
              <span className="text-gray-400">({spreadPercent.toFixed(4)}%)</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 divide-x divide-gray-700">
        {/* Asks (Ventas) */}
        <div>
          <div className="bg-red-500/10 border-b border-gray-700 px-4 py-2">
            <div className="flex items-center justify-between text-xs text-gray-400 uppercase">
              <span>Precio</span>
              <span>Cantidad</span>
              <span>Total</span>
            </div>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {asks.slice(0, 15).map((ask, index) => {
              const widthPercent = (ask.total / maxTotal) * 100
              return (
                <div
                  key={index}
                  className="relative px-4 py-1.5 hover:bg-gray-800/50 transition cursor-pointer group"
                >
                  <div
                    className="absolute right-0 top-0 h-full bg-red-500/20 opacity-30 group-hover:opacity-50 transition"
                    style={{ width: `${widthPercent}%` }}
                  />
                  <div className="relative flex items-center justify-between text-sm">
                    <span className="text-red-400 font-medium">{formatPrice(ask.price)}</span>
                    <span className="text-gray-300">{formatAmount(ask.amount)}</span>
                    <span className="text-gray-400">{formatAmount(ask.total)}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Bids (Compras) */}
        <div>
          <div className="bg-green-500/10 border-b border-gray-700 px-4 py-2">
            <div className="flex items-center justify-between text-xs text-gray-400 uppercase">
              <span>Precio</span>
              <span>Cantidad</span>
              <span>Total</span>
            </div>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {bids.slice(-15).reverse().map((bid, index) => {
              const widthPercent = (bid.total / maxTotal) * 100
              return (
                <div
                  key={index}
                  className="relative px-4 py-1.5 hover:bg-gray-800/50 transition cursor-pointer group"
                >
                  <div
                    className="absolute left-0 top-0 h-full bg-green-500/20 opacity-30 group-hover:opacity-50 transition"
                    style={{ width: `${widthPercent}%` }}
                  />
                  <div className="relative flex items-center justify-between text-sm">
                    <span className="text-green-400 font-medium">{formatPrice(bid.price)}</span>
                    <span className="text-gray-300">{formatAmount(bid.amount)}</span>
                    <span className="text-gray-400">{formatAmount(bid.total)}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Precio actual en el medio */}
      <div className="bg-gray-800 border-t border-gray-700 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-green-400" />
            <span className="text-gray-400 text-sm">Mejor Bid:</span>
            <span className="text-green-400 font-semibold">
              {bids.length > 0 ? formatPrice(bids[bids.length - 1].price) : '--'}
            </span>
          </div>
          <div className="text-center">
            <span className="text-gray-400 text-xs">Precio Actual</span>
            <div className="text-xl font-bold text-white">{formatPrice(currentPrice)}</div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-sm">Mejor Ask:</span>
            <span className="text-red-400 font-semibold">
              {asks.length > 0 ? formatPrice(asks[0].price) : '--'}
            </span>
            <TrendingDown className="h-4 w-4 text-red-400" />
          </div>
        </div>
      </div>
    </div>
  )
}

