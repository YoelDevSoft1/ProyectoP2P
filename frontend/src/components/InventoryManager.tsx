'use client'

import { useState } from 'react'
import { Wallet, TrendingUp, TrendingDown, AlertTriangle, RefreshCw, Plus, Minus } from 'lucide-react'

interface InventoryData {
  currency: string
  available: number
  reserved: number
  total: number
  value_usd: number
  trend?: 'up' | 'down' | 'stable'
}

export function InventoryManager() {
  const [inventory, setInventory] = useState<InventoryData[]>([
    {
      currency: 'USDT',
      available: 50000,
      reserved: 5000,
      total: 55000,
      value_usd: 55000,
      trend: 'stable',
    },
    {
      currency: 'COP',
      available: 200000000,
      reserved: 20000000,
      total: 220000000,
      value_usd: 50000,
      trend: 'up',
    },
    {
      currency: 'VES',
      available: 50000000000,
      reserved: 5000000000,
      total: 55000000000,
      value_usd: 30000,
      trend: 'down',
    },
  ])

  const totalValueUSD = inventory.reduce((sum, inv) => sum + inv.value_usd, 0)
  const totalAvailableUSD = inventory
    .filter((inv) => inv.currency === 'USDT')
    .reduce((sum, inv) => sum + inv.available, 0)

  const getCurrencyInfo = (currency: string) => {
    switch (currency) {
      case 'USDT':
        return { symbol: 'USDT', flag: '💵', color: 'text-green-400', bgColor: 'bg-green-500/20' }
      case 'COP':
        return { symbol: '$', flag: '🇨🇴', color: 'text-blue-400', bgColor: 'bg-blue-500/20' }
      case 'VES':
        return { symbol: 'Bs.', flag: '🇻🇪', color: 'text-yellow-400', bgColor: 'bg-yellow-500/20' }
      default:
        return { symbol: '', flag: '', color: 'text-gray-400', bgColor: 'bg-gray-500/20' }
    }
  }

  const formatCurrency = (value: number, currency: string) => {
    if (currency === 'VES') {
      return value.toLocaleString('es-VE', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
    } else if (currency === 'COP') {
      return value.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
    } else {
      return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }
  }

  const getUtilizationPercentage = (inv: InventoryData) => {
    return inv.total > 0 ? (inv.reserved / inv.total) * 100 : 0
  }

  const getUtilizationColor = (percentage: number) => {
    if (percentage > 80) return 'text-red-400'
    if (percentage > 60) return 'text-yellow-400'
    return 'text-green-400'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Gestión de Inventario</h2>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-all">
          <RefreshCw className="h-4 w-4" />
          Actualizar
        </button>
      </div>

      {/* Resumen Total */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-gray-400">Valor Total (USD)</span>
            <Wallet className="h-5 w-5 text-primary-400" />
          </div>
          <p className="text-3xl font-bold text-white">${totalValueUSD.toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
          <p className="text-sm text-gray-500 mt-2">Inventario completo</p>
        </div>

        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-gray-400">Disponible (USDT)</span>
            <TrendingUp className="h-5 w-5 text-green-400" />
          </div>
          <p className="text-3xl font-bold text-white">{totalAvailableUSD.toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
          <p className="text-sm text-gray-500 mt-2">Para nuevas operaciones</p>
        </div>

        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-gray-400">Reservado</span>
            <AlertTriangle className="h-5 w-5 text-yellow-400" />
          </div>
          <p className="text-3xl font-bold text-white">
            {inventory.reduce((sum, inv) => sum + (inv.reserved / (inv.currency === 'USDT' ? 1 : inv.currency === 'COP' ? 4000 : 1600000)), 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </p>
          <p className="text-sm text-gray-500 mt-2">En operaciones activas</p>
        </div>
      </div>

      {/* Detalle por Moneda */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {inventory.map((inv) => {
          const info = getCurrencyInfo(inv.currency)
          const utilization = getUtilizationPercentage(inv)
          const isLowStock = utilization > 80 || (inv.available / inv.total) < 0.2

          return (
            <div
              key={inv.currency}
              className={`bg-gradient-to-br from-gray-800 to-gray-900 border rounded-xl p-6 ${
                isLowStock ? 'border-red-500/50' : 'border-gray-700'
              }`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{info.flag}</span>
                  <div>
                    <h3 className="text-lg font-bold text-white">{inv.currency}</h3>
                    <p className="text-xs text-gray-400">Inventario</p>
                  </div>
                </div>
                {inv.trend && (
                  <div>
                    {inv.trend === 'up' ? (
                      <TrendingUp className="h-5 w-5 text-green-400" />
                    ) : inv.trend === 'down' ? (
                      <TrendingDown className="h-5 w-5 text-red-400" />
                    ) : (
                      <div className="w-5 h-5 rounded-full bg-gray-400" />
                    )}
                  </div>
                )}
              </div>

              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-400">Disponible</span>
                    <span className="text-white font-semibold">
                      {info.symbol}
                      {formatCurrency(inv.available, inv.currency)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-400">Reservado</span>
                    <span className="text-yellow-400 font-semibold">
                      {info.symbol}
                      {formatCurrency(inv.reserved, inv.currency)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-400">Total</span>
                    <span className="text-white font-semibold">
                      {info.symbol}
                      {formatCurrency(inv.total, inv.currency)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Valor (USD)</span>
                    <span className="text-green-400 font-semibold">${inv.value_usd.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
                  </div>
                </div>

                {/* Barra de Utilización */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-400">Utilización</span>
                    <span className={getUtilizationColor(utilization)}>{utilization.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        utilization > 80
                          ? 'bg-red-500'
                          : utilization > 60
                          ? 'bg-yellow-500'
                          : 'bg-green-500'
                      }`}
                      style={{ width: `${utilization}%` }}
                    />
                  </div>
                </div>

                {/* Alertas */}
                {isLowStock && (
                  <div className="flex items-center gap-2 p-2 bg-red-500/20 border border-red-500/50 rounded-lg">
                    <AlertTriangle className="h-4 w-4 text-red-400" />
                    <span className="text-xs text-red-400">Stock bajo - Considera recargar</span>
                  </div>
                )}

                {/* Acciones Rápidas */}
                <div className="flex gap-2 pt-2 border-t border-gray-700">
                  <button className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-green-600/20 hover:bg-green-600/30 text-green-400 rounded-lg transition-all text-sm">
                    <Plus className="h-4 w-4" />
                    Recargar
                  </button>
                  <button className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 rounded-lg transition-all text-sm">
                    <Minus className="h-4 w-4" />
                    Retirar
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Alertas y Recomendaciones */}
      <div className="bg-gradient-to-r from-yellow-900/30 to-orange-900/20 border border-yellow-700/50 rounded-xl p-6">
        <div className="flex items-start gap-4">
          <AlertTriangle className="h-6 w-6 text-yellow-400 mt-1" />
          <div>
            <h4 className="text-lg font-semibold text-white mb-2">Recomendaciones de Inventario</h4>
            <ul className="text-sm text-gray-300 space-y-1">
              <li>• Mantén un balance equilibrado entre USDT y monedas fiat</li>
              <li>• Monitorea la utilización de inventario en tiempo real</li>
              <li>• Recarga cuando la disponibilidad sea menor al 20%</li>
              <li>• Considera el volumen promedio diario al planificar inventario</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

