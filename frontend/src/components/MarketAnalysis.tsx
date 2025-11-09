'use client'

import { useQuery } from '@tanstack/react-query'
import { TrendingUp, TrendingDown, AlertCircle, Zap, Target, DollarSign } from 'lucide-react'
import api from '@/lib/api'

export function MarketAnalysis() {
  const { data: spreadAnalysis } = useQuery({
    queryKey: ['spread-analysis'],
    queryFn: () => api.getSpreadAnalysis('USDT'),
    refetchInterval: 30000,
  })

  const { data: prices } = useQuery({
    queryKey: ['prices-analysis'],
    queryFn: () => api.getCurrentPrices(),
    refetchInterval: 10000,
  })

  // Simular oportunidades de arbitraje
  const opportunities = [
    {
      id: 1,
      type: 'spread',
      currency: 'COP',
      opportunity: 'Spread alto detectado',
      profit: 2.5,
      risk: 'low',
      action: 'Comprar en mercado, vender a cliente',
    },
    {
      id: 2,
      type: 'arbitrage',
      currency: 'VES',
      opportunity: 'Oportunidad de arbitraje triangular',
      profit: 1.8,
      risk: 'medium',
      action: 'Ejecutar arbitraje automático',
    },
    {
      id: 3,
      type: 'volume',
      currency: 'COP',
      opportunity: 'Alta demanda detectada',
      profit: 3.2,
      risk: 'low',
      action: 'Aumentar inventario COP',
    },
  ]

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'text-green-400 bg-green-500/20 border-green-500/50'
      case 'medium':
        return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/50'
      case 'high':
        return 'text-red-400 bg-red-500/20 border-red-500/50'
      default:
        return 'text-gray-400 bg-gray-500/20 border-gray-500/50'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Análisis de Mercado</h2>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <AlertCircle className="h-4 w-4" />
          <span>Actualizado en tiempo real</span>
        </div>
      </div>

      {/* Análisis de Spread */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {prices && (
          <>
            {prices.COP && (
              <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">🇨🇴</span>
                    <div>
                      <h3 className="text-lg font-bold text-white">COP Market</h3>
                      <p className="text-xs text-gray-400">Análisis de spread</p>
                    </div>
                  </div>
                  {spreadAnalysis?.cop?.spread_percent && (
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                      spreadAnalysis.cop.spread_percent > 2
                        ? 'bg-green-500/20 text-green-400 border border-green-500'
                        : spreadAnalysis.cop.spread_percent > 1
                        ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500'
                        : 'bg-red-500/20 text-red-400 border border-red-500'
                    }`}>
                      {spreadAnalysis.cop.spread_percent.toFixed(2)}%
                    </div>
                  )}
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Precio Compra</span>
                    <span className="text-white font-semibold">${prices.COP.buy_price.toLocaleString('es-CO')}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Precio Venta</span>
                    <span className="text-white font-semibold">${prices.COP.sell_price.toLocaleString('es-CO')}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Spread</span>
                    <span className="text-green-400 font-semibold">{prices.COP.spread.toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Margen</span>
                    <span className="text-primary-400 font-semibold">{prices.COP.margin.toFixed(2)}%</span>
                  </div>
                </div>

                {/* Indicador de Oportunidad */}
                <div className="mt-4 p-3 bg-blue-500/20 border border-blue-500/50 rounded-lg">
                  <div className="flex items-center gap-2">
                    {prices.COP.spread > 2 ? (
                      <>
                        <Zap className="h-4 w-4 text-blue-400" />
                        <span className="text-sm text-blue-400">Oportunidad: Spread favorable para trading</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="h-4 w-4 text-yellow-400" />
                        <span className="text-sm text-yellow-400">Spread bajo - Considera ajustar precios</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {prices.VES && (
              <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">🇻🇪</span>
                    <div>
                      <h3 className="text-lg font-bold text-white">VES Market</h3>
                      <p className="text-xs text-gray-400">Análisis de spread</p>
                    </div>
                  </div>
                  {spreadAnalysis?.ves?.spread_percent && (
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                      spreadAnalysis.ves.spread_percent > 2
                        ? 'bg-green-500/20 text-green-400 border border-green-500'
                        : spreadAnalysis.ves.spread_percent > 1
                        ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500'
                        : 'bg-red-500/20 text-red-400 border border-red-500'
                    }`}>
                      {spreadAnalysis.ves.spread_percent.toFixed(2)}%
                    </div>
                  )}
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Precio Compra</span>
                    <span className="text-white font-semibold">Bs. {prices.VES.buy_price.toLocaleString('es-VE')}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Precio Venta</span>
                    <span className="text-white font-semibold">Bs. {prices.VES.sell_price.toLocaleString('es-VE')}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Spread</span>
                    <span className="text-green-400 font-semibold">{prices.VES.spread.toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Margen</span>
                    <span className="text-primary-400 font-semibold">{prices.VES.margin.toFixed(2)}%</span>
                  </div>
                </div>

                {/* Indicador de Oportunidad */}
                <div className="mt-4 p-3 bg-blue-500/20 border border-blue-500/50 rounded-lg">
                  <div className="flex items-center gap-2">
                    {prices.VES.spread > 2 ? (
                      <>
                        <Zap className="h-4 w-4 text-blue-400" />
                        <span className="text-sm text-blue-400">Oportunidad: Spread favorable para trading</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="h-4 w-4 text-yellow-400" />
                        <span className="text-sm text-yellow-400">Spread bajo - Considera ajustar precios</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Oportunidades de Trading */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-white">Oportunidades Detectadas</h3>
          <span className="px-3 py-1 bg-primary-500/20 text-primary-400 border border-primary-500 rounded-full text-sm font-medium">
            {opportunities.length} activas
          </span>
        </div>

        <div className="space-y-4">
          {opportunities.map((opp) => (
            <div
              key={opp.id}
              className="bg-gray-700/50 border border-gray-600 rounded-lg p-4 hover:border-primary-500 transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`px-3 py-1 rounded-full text-xs font-medium border ${getRiskColor(opp.risk)}`}>
                      {opp.risk.toUpperCase()}
                    </div>
                    <span className="text-sm text-gray-400">{opp.currency}</span>
                    <span className="text-sm font-semibold text-white">{opp.type.toUpperCase()}</span>
                  </div>
                  <h4 className="text-white font-semibold mb-1">{opp.opportunity}</h4>
                  <p className="text-sm text-gray-400 mb-2">{opp.action}</p>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <DollarSign className="h-4 w-4 text-green-400" />
                      <span className="text-sm text-green-400 font-semibold">+{opp.profit}% profit potencial</span>
                    </div>
                  </div>
                </div>
                <button className="ml-4 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-all text-sm font-medium">
                  Ejecutar
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recomendaciones */}
      <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/20 border border-blue-700/50 rounded-xl p-6">
        <div className="flex items-start gap-4">
          <Target className="h-6 w-6 text-blue-400 mt-1" />
          <div>
            <h4 className="text-lg font-semibold text-white mb-2">Recomendaciones de Mercado</h4>
            <ul className="text-sm text-gray-300 space-y-1">
              <li>• Monitorea los spreads en tiempo real para detectar oportunidades</li>
              <li>• Ajusta los márgenes según las condiciones del mercado</li>
              <li>• Considera aumentar inventario cuando detectes alta demanda</li>
              <li>• Ejecuta arbitraje cuando el spread sea mayor al 2%</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

