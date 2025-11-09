'use client'

import { useState, useEffect, useMemo } from 'react'
import { Calculator, ArrowRightLeft, TrendingUp, TrendingDown, Send, Copy, Check } from 'lucide-react'
import { PriceData, Currency, TradeDirection } from '@/types/prices'

interface CurrencyCalculatorProps {
  copData?: PriceData
  vesData?: PriceData
  trm?: number
  whatsappLink?: string | null
  whatsappMessage?: string
}

type Direction = TradeDirection

export function CurrencyCalculator({
  copData,
  vesData,
  trm,
  whatsappLink,
  whatsappMessage = 'Hola, quiero cambiar divisas',
}: CurrencyCalculatorProps) {
  const [amount, setAmount] = useState<string>('')
  const [fromCurrency, setFromCurrency] = useState<Currency>('COP')
  const [toCurrency, setToCurrency] = useState<Currency>('USDT')
  const [direction, setDirection] = useState<Direction>('sell')
  const [copied, setCopied] = useState(false)

  // Calcular resultado
  const result = useMemo(() => {
    if (!amount || parseFloat(amount) <= 0) return null

    const amountNum = parseFloat(amount)
    let calculatedAmount = 0
    let fee = 0
    let feePercentage = 0

    if (direction === 'sell') {
      // Cliente vende COP/VES, recibe USDT
      if (fromCurrency === 'COP' && copData) {
        // Precio de compra (nosotros compramos COP)
        calculatedAmount = amountNum / copData.buy_price
        fee = amountNum * (copData.margin / 100)
        feePercentage = copData.margin
      } else if (fromCurrency === 'VES' && vesData) {
        calculatedAmount = amountNum / vesData.buy_price
        fee = amountNum * (vesData.margin / 100)
        feePercentage = vesData.margin
      } else if (fromCurrency === 'USDT') {
        // Cliente vende USDT, recibe COP/VES
        if (toCurrency === 'COP' && copData) {
          calculatedAmount = amountNum * copData.sell_price
          fee = calculatedAmount * (copData.margin / 100)
          feePercentage = copData.margin
        } else if (toCurrency === 'VES' && vesData) {
          calculatedAmount = amountNum * vesData.sell_price
          fee = calculatedAmount * (vesData.margin / 100)
          feePercentage = vesData.margin
        }
      }
    } else {
      // Cliente compra USDT con COP/VES
      if (fromCurrency === 'COP' && copData) {
        calculatedAmount = amountNum / copData.sell_price
        fee = amountNum * (copData.margin / 100)
        feePercentage = copData.margin
      } else if (fromCurrency === 'VES' && vesData) {
        calculatedAmount = amountNum / vesData.sell_price
        fee = amountNum * (vesData.margin / 100)
        feePercentage = vesData.margin
      }
    }

    return {
      amount: calculatedAmount,
      fee,
      feePercentage,
      total: direction === 'sell' && fromCurrency !== 'USDT' 
        ? calculatedAmount 
        : calculatedAmount - fee,
    }
  }, [amount, fromCurrency, toCurrency, direction, copData, vesData])

  // Auto-cambiar dirección cuando se cambian las monedas
  useEffect(() => {
    if (fromCurrency === 'USDT') {
      setDirection('sell')
      if (toCurrency === 'USDT') setToCurrency('COP')
    } else if (toCurrency === 'USDT') {
      setDirection('buy')
      if (fromCurrency === 'USDT') setFromCurrency('COP')
    }
  }, [fromCurrency, toCurrency])

  const formatCurrency = (value: number, currency: Currency) => {
    if (currency === 'USDT') {
      return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 6 })
    } else if (currency === 'COP') {
      return value.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
    } else {
      return value.toLocaleString('es-VE', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
    }
  }

  const getCurrencySymbol = (currency: Currency) => {
    if (currency === 'USDT') return 'USDT'
    if (currency === 'COP') return '$'
    return 'Bs.'
  }

  const handleCopy = () => {
    if (!result) return
    const text = `Quiero cambiar ${formatCurrency(parseFloat(amount), fromCurrency)} ${fromCurrency} por ${formatCurrency(result.total, toCurrency)} ${toCurrency}`
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleWhatsApp = () => {
    if (!whatsappLink || !result) return
    const message = `${whatsappMessage}\n\nQuiero cambiar:\n${formatCurrency(parseFloat(amount), fromCurrency)} ${fromCurrency}\nPor: ${formatCurrency(result.total, toCurrency)} ${toCurrency}`
    window.open(`${whatsappLink.split('?')[0]}?text=${encodeURIComponent(message)}`, '_blank')
  }

  const currentData = fromCurrency === 'COP' ? copData : fromCurrency === 'VES' ? vesData : null
  const isPositive = result && result.amount > 0

  return (
    <div className="bg-gradient-to-br from-gray-800 via-gray-800 to-gray-900 rounded-2xl p-8 border border-gray-700 shadow-2xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-primary-600/20 rounded-lg">
          <Calculator className="h-6 w-6 text-primary-400" />
        </div>
        <div>
          <h3 className="text-2xl font-bold text-white">Calculadora de Cambio</h3>
          <p className="text-sm text-gray-400">Calcula tu cambio al instante</p>
        </div>
      </div>

      {/* Dirección del cambio */}
      <div className="mb-6">
        <div className="flex gap-2 p-1 bg-gray-700/50 rounded-lg">
          <button
            onClick={() => setDirection('sell')}
            className={`flex-1 px-4 py-2 rounded-md font-medium transition-all ${
              direction === 'sell'
                ? 'bg-primary-600 text-white shadow-lg'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Vender {fromCurrency !== 'USDT' ? fromCurrency : toCurrency}
          </button>
          <button
            onClick={() => setDirection('buy')}
            className={`flex-1 px-4 py-2 rounded-md font-medium transition-all ${
              direction === 'buy'
                ? 'bg-primary-600 text-white shadow-lg'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Comprar {toCurrency === 'USDT' ? 'USDT' : toCurrency}
          </button>
        </div>
      </div>

      {/* Input de monto */}
      <div className="space-y-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">
            Monto a {direction === 'sell' ? 'vender' : 'cambiar'}
          </label>
          <div className="relative">
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              className="w-full px-4 py-4 bg-gray-700/50 border border-gray-600 rounded-lg text-2xl font-bold text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <div className="absolute right-4 top-1/2 -translate-y-1/2">
              <select
                value={fromCurrency}
                onChange={(e) => setFromCurrency(e.target.value as Currency)}
                className="bg-gray-800 border border-gray-600 rounded-md px-3 py-1 text-white font-medium focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="COP">COP</option>
                <option value="VES">VES</option>
                <option value="USDT">USDT</option>
              </select>
            </div>
          </div>
        </div>

        {/* Flecha de intercambio */}
        <div className="flex justify-center my-2">
          <button
            onClick={() => {
              const temp = fromCurrency
              setFromCurrency(toCurrency)
              setToCurrency(temp)
            }}
            className="p-2 bg-gray-700 hover:bg-gray-600 rounded-full transition-all hover:scale-110"
          >
            <ArrowRightLeft className="h-5 w-5 text-gray-400" />
          </button>
        </div>

        {/* Resultado */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">
            Recibirás
          </label>
          <div className="relative">
            <div
              className={`w-full px-4 py-4 bg-gradient-to-r ${
                isPositive
                  ? 'from-green-900/30 to-green-800/20 border-green-700'
                  : 'from-gray-700/50 to-gray-700/30 border-gray-600'
              } border rounded-lg text-2xl font-bold text-white`}
            >
              {result && result.total > 0 ? (
                <div className="flex items-center justify-between">
                  <span>
                    {getCurrencySymbol(toCurrency)}{' '}
                    {formatCurrency(result.total, toCurrency)} {toCurrency}
                  </span>
                  {isPositive && (
                    <TrendingUp className="h-6 w-6 text-green-400" />
                  )}
                </div>
              ) : (
                <span className="text-gray-500">--</span>
              )}
            </div>
            <div className="absolute right-4 top-1/2 -translate-y-1/2">
              <select
                value={toCurrency}
                onChange={(e) => setToCurrency(e.target.value as Currency)}
                className="bg-gray-800 border border-gray-600 rounded-md px-3 py-1 text-white font-medium focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="USDT">USDT</option>
                <option value="COP">COP</option>
                <option value="VES">VES</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Información de comisión */}
      {result && result.total > 0 && currentData && (
        <div className="mb-6 p-4 bg-gray-700/30 rounded-lg border border-gray-600">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between text-gray-400">
              <span>Comisión ({result.feePercentage.toFixed(2)}%)</span>
              <span className="text-white font-medium">
                {getCurrencySymbol(fromCurrency)}{formatCurrency(result.fee, fromCurrency)}
              </span>
            </div>
            <div className="flex justify-between text-gray-400">
              <span>Tasa de cambio</span>
              <span className="text-white font-medium">
                {direction === 'sell' && fromCurrency !== 'USDT'
                  ? `1 ${fromCurrency} = ${(1 / currentData.buy_price).toFixed(6)} USDT`
                  : `1 USDT = ${currentData.sell_price.toLocaleString()} ${toCurrency}`}
              </span>
            </div>
            {fromCurrency === 'COP' && trm && (
              <div className="flex justify-between text-gray-400 pt-2 border-t border-gray-600">
                <span>TRM Oficial</span>
                <span className="text-white font-medium">
                  ${trm.toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Botones de acción */}
      {result && result.total > 0 && (
        <div className="flex gap-3">
          {whatsappLink && (
            <button
              onClick={handleWhatsApp}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-all hover:scale-105 shadow-lg hover:shadow-green-600/50"
            >
              <Send className="h-5 w-5" />
              Contactar por WhatsApp
            </button>
          )}
          <button
            onClick={handleCopy}
            className="px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white font-semibold rounded-lg transition-all"
          >
            {copied ? (
              <Check className="h-5 w-5 text-green-400" />
            ) : (
              <Copy className="h-5 w-5" />
            )}
          </button>
        </div>
      )}

      {/* Mensaje de ayuda */}
      {(!copData && fromCurrency === 'COP') || (!vesData && fromCurrency === 'VES') ? (
        <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-700/50 rounded-lg">
          <p className="text-sm text-yellow-400">
            Los precios se están cargando. Por favor espera un momento.
          </p>
        </div>
      ) : null}
    </div>
  )
}

