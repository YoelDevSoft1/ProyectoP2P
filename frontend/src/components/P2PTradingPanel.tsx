'use client'

import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2, RefreshCw, CheckCircle2, AlertTriangle } from 'lucide-react'

import api from '@/lib/api'

const PAYMENT_METHODS: Record<string, string[]> = {
  COP: ['Nequi', 'Bancolombia', 'DaviPlata', 'PSE', 'BankTransfer'],
  VES: ['Banesco', 'Mercantil', 'BDV', 'Zelle', 'BankTransfer'],
}

export function P2PTradingPanel() {
  const [asset, setAsset] = useState('USDT')
  const [fiat, setFiat] = useState('COP')
  const [tradeType, setTradeType] = useState<'BUY' | 'SELL'>('BUY')
  const [amount, setAmount] = useState('')
  const [price, setPrice] = useState('')
  const [minAmount, setMinAmount] = useState('')
  const [maxAmount, setMaxAmount] = useState('')
  const [paymentMethods, setPaymentMethods] = useState<string[]>([])
  const [tradeFeedback, setTradeFeedback] = useState<{ success: boolean; message: string } | null>(null)
  const [cancelFeedback, setCancelFeedback] = useState<{ success: boolean; message: string } | null>(null)
  const [loadingTrade, setLoadingTrade] = useState(false)
  const [loadingCancel, setLoadingCancel] = useState(false)
  const [tradeIdToCancel, setTradeIdToCancel] = useState('')

  const { data: ordersData, isFetching: loadingOrders, refetch: refetchOrders } = useQuery({
    queryKey: ['p2p-orders'],
    queryFn: async () => {
      try {
        return await api.getP2POrders()
      } catch (error) {
        console.error('Error fetching P2P orders:', error)
        throw error
      }
    },
    refetchInterval: 60000,
  })

  const availableMethods = useMemo(() => PAYMENT_METHODS[fiat] || PAYMENT_METHODS.COP, [fiat])

  const togglePaymentMethod = (method: string) => {
    setPaymentMethods((prev) =>
      prev.includes(method) ? prev.filter((m) => m !== method) : [...prev, method]
    )
  }

  const resetFeedback = () => {
    setTradeFeedback(null)
    setCancelFeedback(null)
  }

  const handleExecuteTrade = async () => {
    resetFeedback()
    if (!amount || !price) {
      setTradeFeedback({ success: false, message: 'Debes ingresar monto y precio para publicar.' })
      return
    }

    const parsedAmount = parseFloat(amount)
    const parsedPrice = parseFloat(price)

    if (Number.isNaN(parsedAmount) || Number.isNaN(parsedPrice)) {
      setTradeFeedback({ success: false, message: 'Monto y precio deben ser números válidos.' })
      return
    }

    setLoadingTrade(true)
    try {
      const response = await api.executeP2PTrade({
        asset,
        fiat,
        trade_type: tradeType,
        amount: parsedAmount,
        price: parsedPrice,
        payment_methods: paymentMethods,
        min_amount: minAmount ? parseFloat(minAmount) : undefined,
        max_amount: maxAmount ? parseFloat(maxAmount) : undefined,
      })
      setTradeFeedback({ success: true, message: response?.message || 'Trade publicado correctamente.' })
      await refetchOrders()
      setAmount('')
      setPrice('')
      setMinAmount('')
      setMaxAmount('')
    } catch (error: any) {
      console.error('Error executing P2P trade:', error)
      setTradeFeedback({ success: false, message: error?.response?.data?.detail || error?.message || 'No se pudo ejecutar el trade.' })
    } finally {
      setLoadingTrade(false)
    }
  }

  const handleCancelTrade = async () => {
    resetFeedback()
    const parsedId = parseInt(tradeIdToCancel, 10)
    if (Number.isNaN(parsedId)) {
      setCancelFeedback({ success: false, message: 'Ingresa un ID de trade válido.' })
      return
    }

    setLoadingCancel(true)
    try {
      const response = await api.cancelP2PTrade(parsedId)
      setCancelFeedback({ success: true, message: response?.message || 'Trade cancelado correctamente.' })
      await refetchOrders()
      setTradeIdToCancel('')
    } catch (error: any) {
      console.error('Error cancelling P2P trade:', error)
      setCancelFeedback({ success: false, message: error?.response?.data?.detail || error?.message || 'No se pudo cancelar el trade.' })
    } finally {
      setLoadingCancel(false)
    }
  }

  const orders = ordersData?.orders || []

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-primary-400 uppercase tracking-wide">Automatización Real</p>
          <h2 className="text-2xl font-bold text-white">P2P Trading Control</h2>
          <p className="text-gray-400 text-sm mt-1">
            Publica, monitorea y cancela anuncios reales directamente desde el dashboard.
          </p>
        </div>
        <button
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-800 text-gray-200 text-sm hover:bg-gray-700"
          onClick={() => refetchOrders()}
          disabled={loadingOrders}
        >
          <RefreshCw className={`h-4 w-4 ${loadingOrders ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-400">Asset</label>
              <select
                value={asset}
                onChange={(e) => setAsset(e.target.value)}
                className="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="USDT">USDT</option>
                <option value="BTC">BTC</option>
                <option value="ETH">ETH</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-gray-400">Fiat</label>
              <select
                value={fiat}
                onChange={(e) => setFiat(e.target.value)}
                className="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="COP">COP</option>
                <option value="VES">VES</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-gray-400">Tipo</label>
              <select
                value={tradeType}
                onChange={(e) => setTradeType(e.target.value as 'BUY' | 'SELL')}
                className="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="BUY">Compra</option>
                <option value="SELL">Venta</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-gray-400">Métodos de Pago</label>
              <div className="mt-2 flex flex-wrap gap-2">
                {availableMethods.map((method) => {
                  const active = paymentMethods.includes(method)
                  return (
                    <button
                      key={method}
                      type="button"
                      onClick={() => togglePaymentMethod(method)}
                      className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                        active
                          ? 'bg-primary-600 text-white border-primary-300'
                          : 'bg-gray-800 text-gray-300 border-gray-700 hover:border-primary-400'
                      }`}
                    >
                      {method}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-400">Cantidad</label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="text-sm text-gray-400">Precio</label>
              <input
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="0.00"
                className="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="text-sm text-gray-400">Min Amount</label>
              <input
                type="number"
                value={minAmount}
                onChange={(e) => setMinAmount(e.target.value)}
                placeholder="Opcional"
                className="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="text-sm text-gray-400">Max Amount</label>
              <input
                type="number"
                value={maxAmount}
                onChange={(e) => setMaxAmount(e.target.value)}
                placeholder="Opcional"
                className="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <button
            onClick={handleExecuteTrade}
            disabled={loadingTrade}
            className="w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-500 text-white font-semibold rounded-lg py-3 transition disabled:opacity-60"
          >
            {loadingTrade && <Loader2 className="h-5 w-5 animate-spin" />}
            {loadingTrade ? 'Publicando...' : 'Publicar Trade Real'}
          </button>

          {tradeFeedback && (
            <div
              className={`flex items-center gap-3 px-4 py-3 rounded-lg border text-sm ${
                tradeFeedback.success
                  ? 'bg-green-900/30 border-green-500/60 text-green-100'
                  : 'bg-red-900/30 border-red-500/60 text-red-100'
              }`}
            >
              {tradeFeedback.success ? (
                <CheckCircle2 className="h-5 w-5" />
              ) : (
                <AlertTriangle className="h-5 w-5" />
              )}
              <span>{tradeFeedback.message}</span>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="bg-gray-800 rounded-2xl p-4 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-2">Cancelar Trade</h3>
            <p className="text-xs text-gray-400 mb-3">
              Usa el ID del trade guardado en base de datos para ejecutar la cancelación.
            </p>
            <input
              type="number"
              placeholder="ID de trade"
              value={tradeIdToCancel}
              onChange={(e) => setTradeIdToCancel(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <button
              onClick={handleCancelTrade}
              disabled={loadingCancel}
              className="mt-3 w-full flex items-center justify-center gap-2 bg-gray-700 hover:bg-gray-600 text-white font-medium rounded-lg py-2.5 transition disabled:opacity-60"
            >
              {loadingCancel && <Loader2 className="h-4 w-4 animate-spin" />}
              {loadingCancel ? 'Cancelando...' : 'Cancelar Trade'}
            </button>
            {cancelFeedback && (
              <div
                className={`mt-3 flex items-center gap-2 text-sm ${
                  cancelFeedback.success ? 'text-green-300' : 'text-red-300'
                }`}
              >
                {cancelFeedback.success ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                <span>{cancelFeedback.message}</span>
              </div>
            )}
          </div>

          <div className="bg-gray-800 rounded-2xl p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-lg font-semibold text-white">Órdenes Activas</h3>
                <p className="text-xs text-gray-400">Sincronizadas desde Binance P2P</p>
              </div>
              {loadingOrders && <Loader2 className="h-4 w-4 animate-spin text-primary-400" />}
            </div>
            {orders.length === 0 ? (
              <p className="text-sm text-gray-400">No hay órdenes activas reportadas.</p>
            ) : (
              <ul className="space-y-3 max-h-64 overflow-auto pr-1">
                {orders.slice(0, 6).map((order: any) => (
                  <li key={order.order_id} className="bg-gray-900/70 border border-gray-700 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-300 font-medium">#{order.order_id}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-primary-600/20 text-primary-200">Activo</span>
                    </div>
                    {order.raw_html && (
                      <p className="text-xs text-gray-500 mt-2 line-clamp-2">{order.raw_html}</p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
