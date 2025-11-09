'use client'

import { useState, useMemo } from 'react'
import { Calculator, ArrowRightLeft, TrendingUp, Send, Copy, Check } from 'lucide-react'
import { PriceData, Currency, TradeDirection } from '@/types/prices'

interface CurrencyCalculatorProps {
  copData?: PriceData
  vesData?: PriceData
  trm?: number
  whatsappLink?: string | null
  whatsappMessage?: string
}

type Direction = TradeDirection

type FiatCurrency = Exclude<Currency, 'USDT'>

interface ConversionStep {
  from: Currency
  to: Currency
  rate: number
  priceType: 'buy' | 'sell'
  data: PriceData
}

interface ConversionResult {
  total: number
  originalAmount: number
  steps: ConversionStep[]
  feePercentage: number
}

const isFiatCurrency = (currency: Currency): currency is FiatCurrency =>
  currency === 'COP' || currency === 'VES'

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

  const requiredFiats = useMemo(() => {
    const needed: FiatCurrency[] = []
    if (isFiatCurrency(fromCurrency)) {
      needed.push(fromCurrency)
    }
    if (isFiatCurrency(toCurrency) && !needed.includes(toCurrency)) {
      needed.push(toCurrency)
    }
    return needed
  }, [fromCurrency, toCurrency])

  const missingData = useMemo(() => {
    return requiredFiats.filter((currency) => {
      if (currency === 'COP') return !copData
      if (currency === 'VES') return !vesData
      return false
    })
  }, [requiredFiats, copData, vesData])

  // Calcular resultado
  const result = useMemo<ConversionResult | null>(() => {
    if (!amount) return null
    const amountNum = parseFloat(amount)
    if (!Number.isFinite(amountNum) || amountNum <= 0) return null
    if (missingData.length > 0) return null

    const steps: ConversionStep[] = []
    let total = amountNum

    const getFiatData = (currency: FiatCurrency) => (currency === 'COP' ? copData : vesData)

    const convertUsdtToFiat = (currency: FiatCurrency) => {
      const data = getFiatData(currency)
      if (!data || data.buy_price <= 0) return false
      total = total * data.buy_price
      steps.push({ from: 'USDT', to: currency, rate: data.buy_price, priceType: 'buy', data })
      return true
    }

    const convertFiatToUsdt = (currency: FiatCurrency) => {
      const data = getFiatData(currency)
      if (!data || data.sell_price <= 0) return false
      total = total / data.sell_price
      steps.push({ from: currency, to: 'USDT', rate: data.sell_price, priceType: 'sell', data })
      return true
    }

    if (fromCurrency === toCurrency) {
      return {
        total,
        originalAmount: amountNum,
        steps,
        feePercentage: 0,
      }
    }

    if (fromCurrency === 'USDT' && isFiatCurrency(toCurrency)) {
      if (!convertUsdtToFiat(toCurrency)) return null
    } else if (isFiatCurrency(fromCurrency) && toCurrency === 'USDT') {
      if (!convertFiatToUsdt(fromCurrency)) return null
    } else if (isFiatCurrency(fromCurrency) && isFiatCurrency(toCurrency)) {
      if (!convertFiatToUsdt(fromCurrency)) return null
      if (!convertUsdtToFiat(toCurrency)) return null
    } else {
      return null
    }

    const feePercentage = steps.reduce((acc, step) => acc + (step.data.margin ?? 0), 0)

    return {
      total,
      originalAmount: amountNum,
      steps,
      feePercentage,
    }
  }, [amount, fromCurrency, toCurrency, copData, vesData, missingData.length])

  const formatCurrency = (value: number, currency: Currency) => {
    // Sin decimales para todos los resultados
    if (currency === 'USDT') {
      return Math.round(value).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
    } else if (currency === 'COP') {
      return Math.round(value).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
    } else {
      return Math.round(value).toLocaleString('es-VE', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
    }
  }

  const getCurrencySymbol = (currency: Currency) => {
    if (currency === 'USDT') return 'USDT'
    if (currency === 'COP') return '$'
    return 'Bs.'
  }

  const rateDetails = useMemo(() => {
    if (!result?.steps.length) return []

    return result.steps
      .map((step, index) => {
        const fiatCurrency = step.priceType === 'buy' ? step.to : step.from
        if (!isFiatCurrency(fiatCurrency)) return null

        const label = step.priceType === 'buy'
          ? `Precio de compra ${fiatCurrency}`
          : `Precio de venta ${fiatCurrency}`

        const formattedValue = `1 USDT = ${getCurrencySymbol(fiatCurrency)} ${formatCurrency(step.rate, fiatCurrency)} ${fiatCurrency}`

        return {
          key: `${fiatCurrency}-${step.priceType}-${index}`,
          label,
          value: formattedValue,
        }
      })
      .filter((detail): detail is { key: string; label: string; value: string } => Boolean(detail))
  }, [result])

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

  const handleDirectionChange = (newDirection: Direction) => {
    setDirection(newDirection)

    if (newDirection === 'sell') {
      if (fromCurrency !== 'USDT') {
        setFromCurrency('USDT')
      }
      if (toCurrency === 'USDT') {
        setToCurrency(isFiatCurrency(fromCurrency) ? fromCurrency : 'COP')
      }
    } else {
      if (toCurrency !== 'USDT') {
        setToCurrency('USDT')
      }
      if (fromCurrency === 'USDT') {
        setFromCurrency('COP')
      }
    }
  }

  const isPositive = (result?.total ?? 0) > 0
  const parsedAmount = parseFloat(amount)
  const hasAmount = Number.isFinite(parsedAmount) && parsedAmount > 0
  const trmValue = typeof trm === 'number' ? trm : null
  const showTrm = trmValue !== null && requiredFiats.includes('COP')

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
            onClick={() => handleDirectionChange('sell')}
            className={`flex-1 px-4 py-2 rounded-md font-medium transition-all ${
              direction === 'sell'
                ? 'bg-primary-600 text-white shadow-lg'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Vender USDT
          </button>
          <button
            onClick={() => handleDirectionChange('buy')}
            className={`flex-1 px-4 py-2 rounded-md font-medium transition-all ${
              direction === 'buy'
                ? 'bg-primary-600 text-white shadow-lg'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Comprar USDT
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
      {result && result.total > 0 && rateDetails.length > 0 && (
        <div className="mb-6 p-4 bg-gray-700/30 rounded-lg border border-gray-600">
          <div className="space-y-3 text-sm">
            {rateDetails.map((detail) => (
              <div key={detail.key} className="flex justify-between text-gray-400">
                <span>{detail.label}</span>
                <span className="text-white font-medium">{detail.value}</span>
              </div>
            ))}
            {result.feePercentage > 0 && (
              <div className="flex justify-between text-gray-400 pt-2 border-t border-gray-600">
                <span>Margen aplicado total</span>
                <span className="text-white font-medium">
                  Incluido ({result.feePercentage.toFixed(2)}%)
                </span>
              </div>
            )}
            {showTrm && (
              <div className="flex justify-between text-gray-400 pt-2 border-t border-gray-600">
                <span>TRM Oficial</span>
                <span className="text-white font-medium">
                  ${Math.round(trmValue ?? 0).toLocaleString('es-CO')}
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

      {/* Mensajes de ayuda / error */}
      {missingData.length > 0 && (
        <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-700/50 rounded-lg">
          <p className="text-sm text-yellow-400">
            {`Las tasas de ${missingData.join(' / ')} se están cargando. Por favor espera un momento.`}
          </p>
        </div>
      )}

      {missingData.length === 0 && hasAmount && !result && (
        <div className="mt-4 p-3 bg-red-900/20 border border-red-700/50 rounded-lg">
          <p className="text-sm text-red-400">
            No pudimos calcular esta conversión con las tasas actuales. Intenta nuevamente en unos segundos.
          </p>
        </div>
      )}
    </div>
  )
}

