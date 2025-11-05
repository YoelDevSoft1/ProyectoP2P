'use client'

import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import {
  ArrowRight,
  TrendingUp,
  Shield,
  Zap,
  Clock,
  DollarSign,
  MessageCircle,
  CheckCircle,
  Star,
} from 'lucide-react'

import api from '@/lib/api'
import { PriceCard } from '@/components/PriceCard'
import { StatsBar } from '@/components/StatsBar'
import { WhatsAppButton } from '@/components/WhatsAppButton'

type PriceData = {
  asset: string
  fiat: string
  buy_price: number
  sell_price: number
  market_buy: number
  market_sell: number
  spread: number
  margin: number
  timestamp: string
  trm?: number
}

type PriceResponse = Record<string, PriceData>

type TradeStats = {
  period_days: number
  total_trades: number
  completed: number
  pending: number
  failed: number
  automated_trades: number
  manual_trades: number
  total_profit: number
  total_volume_usd: number
  average_profit_per_trade: number
  success_rate: number
  by_currency?: Record<string, { count: number; volume: number; profit: number }>
}

type TrmResponse = {
  current: number
  currency: string
  last_updated: string
  change_percentage: number
  history: Array<{ date: string; value: number }>
}

interface LandingPageProps {
  initialPrices: PriceResponse | null
  initialTrm: TrmResponse | null
  initialStats: TradeStats | null
}

export default function LandingPage({
  initialPrices,
  initialTrm,
  initialStats,
}: LandingPageProps) {
  const { data: prices, isLoading: pricesLoading, error: pricesError } = useQuery({
    queryKey: ['prices'],
    queryFn: () => api.getCurrentPrices(),
    refetchInterval: 10000,
    initialData: initialPrices ?? undefined,
    retry: 1,
    retryDelay: 2000,
    refetchOnWindowFocus: false,
  })
  
  // Log errors if they occur
  if (pricesError) {
    console.error('Error fetching prices:', pricesError)
  }

  const { data: trmData, error: trmError } = useQuery({
    queryKey: ['trm'],
    queryFn: () => api.getTRM(),
    refetchInterval: 300000,
    initialData: initialTrm ?? undefined,
    retry: 1,
    retryDelay: 2000,
    refetchOnWindowFocus: false,
  })
  
  // Log errors if they occur
  if (trmError) {
    console.error('Error fetching TRM:', trmError)
  }

  const { data: stats, error: statsError } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.getTradeStats(7),
    refetchInterval: 60000,
    initialData: initialStats ?? undefined,
    retry: 1,
    retryDelay: 2000,
    refetchOnWindowFocus: false,
  })
  
  // Log errors if they occur
  if (statsError) {
    console.error('Error fetching stats:', statsError)
  }

  const whatsappNumber = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || ''
  const whatsappMessage =
    process.env.NEXT_PUBLIC_WHATSAPP_MESSAGE ||
    'Hola, quiero cambiar divisas con la mejor tasa del mercado 💰'

  const { whatsappLink, sanitizedPhone } = useMemo(() => {
    if (!whatsappNumber) return { whatsappLink: null, sanitizedPhone: '' }

    const numericPhone = whatsappNumber.replace(/\D/g, '')
    if (!numericPhone) return { whatsappLink: null, sanitizedPhone: '' }

    return {
      whatsappLink: `https://wa.me/${numericPhone}?text=${encodeURIComponent(whatsappMessage)}`,
      sanitizedPhone: numericPhone,
    }
  }, [whatsappNumber, whatsappMessage])

  // Usar datos iniciales si hay error en la query
  const safePrices = pricesError ? initialPrices : prices
  const safeTrm = trmError ? initialTrm : trmData
  const safeStats = statsError ? initialStats : stats

  const highlightedCopPrice = safePrices?.COP?.sell_price ?? null
  const highlightedVesPrice = safePrices?.VES?.sell_price ?? null

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <nav className="bg-gray-900/80 backdrop-blur-md border-b border-primary-500/20 fixed w-full top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <div className="bg-primary-600 p-2 rounded-lg">
                <TrendingUp className="h-6 w-6 text-white" />
              </div>
              <div>
                <span className="text-xl font-bold text-white">CambioExpress</span>
                <p className="text-xs text-primary-400">Divisas en tiempo real, sin sorpresas</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {whatsappLink && (
                <a
                  href={whatsappLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hidden md:flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-all hover:scale-105"
                >
                  <MessageCircle className="h-5 w-5" />
                  Contactar
                </a>
              )}
              <Link
                href="/dashboard"
                className="px-4 py-2 text-primary-400 hover:text-primary-300 font-medium transition-colors"
              >
                Panel
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-600/20 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-primary-600/20 rounded-full blur-3xl"></div>
        </div>

        <div className="max-w-7xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600/20 border border-primary-500/30 rounded-full mb-6">
            <Star className="h-4 w-4 text-primary-400 fill-current" />
            <span className="text-primary-300 text-sm font-medium">
              {safeStats?.completed
                ? `+${safeStats.completed} operaciones exitosas en los últimos ${safeStats.period_days} días`
                : 'Operaciones monitoreadas 24/7'}
            </span>
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold text-white mb-6 leading-tight">
            Las <span className="text-primary-500 relative">
              Mejores Tasas
              <div className="absolute -bottom-2 left-0 right-0 h-1 bg-primary-500/50"></div>
            </span>
            <br />
            para Cambiar tus Divisas
          </h1>

          <p className="text-xl md:text-2xl text-gray-300 mb-10 max-w-3xl mx-auto leading-relaxed">
            Datos en vivo directamente de Binance P2P y TRM oficial. Convierte{' '}
            <span className="text-white font-semibold">COP</span> y{' '}
            <span className="text-white font-semibold">VES</span> a{' '}
            <span className="text-white font-semibold">USDT</span> sin esperas ni tasas escondidas.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            {whatsappLink && (
              <a
                href={whatsappLink}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-center gap-3 px-8 py-4 bg-green-600 hover:bg-green-700 text-white rounded-xl font-bold text-lg transition-all hover:scale-105 shadow-lg hover:shadow-green-600/50"
              >
                <MessageCircle className="h-6 w-6" />
                Cambiar Ahora por WhatsApp
                <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </a>
            )}

            <button
              onClick={() => document.getElementById('tasas')?.scrollIntoView({ behavior: 'smooth' })}
              className="flex items-center gap-2 px-8 py-4 bg-gray-800 hover:bg-gray-700 border border-primary-500/30 text-white rounded-xl font-semibold text-lg transition-all"
            >
              Ver Tasas en Vivo
              <TrendingUp className="h-5 w-5" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            <div className="flex flex-col items-center gap-3 p-6 bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl">
              <div className="p-3 bg-primary-600/20 rounded-lg">
                <DollarSign className="h-8 w-8 text-primary-400" />
              </div>
              <h3 className="text-lg font-bold text-white">Mejor Tasa Verificada</h3>
              <p className="text-gray-400 text-sm">
                Spread optimizado con margen fijo:{' '}
                <span className="text-white font-semibold">
                  {safePrices?.COP ? `${safePrices?.COP.margin.toFixed(2)}%` : '---'}
                </span>{' '}
                COP /{' '}
                <span className="text-white font-semibold">
                  {safePrices?.VES ? `${safePrices?.VES.margin.toFixed(2)}%` : '---'}
                </span>{' '}
                VES.
              </p>
            </div>

            <div className="flex flex-col items-center gap-3 p-6 bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl">
              <div className="p-3 bg-green-600/20 rounded-lg">
                <Clock className="h-8 w-8 text-green-400" />
              </div>
              <h3 className="text-lg font-bold text-white">Operación en Minutos</h3>
              <p className="text-gray-400 text-sm">
                Workflow automatizado con confirmación inmediata y seguimiento en el panel profesional.
              </p>
            </div>

            <div className="flex flex-col items-center gap-3 p-6 bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl">
              <div className="p-3 bg-blue-600/20 rounded-lg">
                <Shield className="h-8 w-8 text-blue-400" />
              </div>
              <h3 className="text-lg font-bold text-white">100% Transparente</h3>
              <p className="text-gray-400 text-sm">
                Respaldo con Binance P2P y monitoreo de riesgo. Sin montos ocultos ni sorpresas de último minuto.
              </p>
            </div>
          </div>

          {(highlightedCopPrice || highlightedVesPrice || safeTrm?.current) && (
            <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
              {highlightedCopPrice && (
                <div className="bg-gray-900/60 border border-primary-500/30 rounded-xl p-6">
                  <p className="text-sm text-primary-300 uppercase tracking-wide mb-2">
                    Venta USDT {'>'} COP (cliente recibe)
                  </p>
                  <p className="text-3xl font-bold text-white">
                    ${highlightedCopPrice.toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                  </p>
                  <p className="text-sm text-gray-400 mt-2">
                    Cotización en vivo actualizada {safePrices?.COP?.timestamp ? new Date(safePrices?.COP.timestamp).toLocaleTimeString('es-CO') : 'en tiempo real'}.
                  </p>
                </div>
              )}
              {highlightedVesPrice && (
                <div className="bg-gray-900/60 border border-primary-500/30 rounded-xl p-6">
                  <p className="text-sm text-primary-300 uppercase tracking-wide mb-2">
                    Venta USDT {'>'} VES (cliente recibe)
                  </p>
                  <p className="text-3xl font-bold text-white">
                    Bs. {highlightedVesPrice.toLocaleString('es-VE', { minimumFractionDigits: 2 })}
                  </p>
                  <p className="text-sm text-gray-400 mt-2">
                    Mercado local monitoreado cada 10 segundos para mantener spread competitivo.
                  </p>
                </div>
              )}
              {safeTrm?.current && (
                <div className="bg-gray-900/60 border border-primary-500/30 rounded-xl p-6">
                  <p className="text-sm text-primary-300 uppercase tracking-wide mb-2">
                    TRM Oficial Colombia (USD)
                  </p>
                  <p className="text-3xl font-bold text-white">
                    ${safeTrm.current.toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                  </p>
                  <p className="text-sm text-gray-400 mt-2">
                    Variación {safeTrm.change_percentage >= 0 ? '+' : ''}
                    {safeTrm.change_percentage} % en {safeTrm.history?.length ?? 0} días.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      <section id="tasas" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-900/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">Tasas en Tiempo Real</h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Cotizaciones actualizadas automáticamente cada 10 segundos desde la API oficial de Binance P2P.
            </p>
            <div className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-green-600/20 border border-green-500/30 rounded-full">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-green-400 text-sm font-medium">
                Última actualización:{' '}
                {safePrices?.COP?.timestamp
                  ? new Date(safePrices?.COP.timestamp).toLocaleTimeString('es-CO')
                  : 'en vivo'}
              </span>
            </div>
          </div>

          {pricesLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {[1, 2].map((i) => (
                <div key={i} className="bg-gray-800 rounded-xl p-8 animate-pulse">
                  <div className="h-8 bg-gray-700 rounded w-1/3 mb-4"></div>
                  <div className="h-12 bg-gray-700 rounded w-1/2 mb-2"></div>
                  <div className="h-6 bg-gray-700 rounded w-2/3"></div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {safePrices?.COP && (
                <PriceCard currency="COP" data={safePrices?.COP} trm={safeTrm?.current} />
              )}
              {safePrices?.VES && (
                <PriceCard currency="VES" data={safePrices?.VES} />
              )}
            </div>
          )}
        </div>
      </section>

      <StatsBar initialStats={stats ?? initialStats ?? null} />

      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-900">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
              ¿Por qué ExpressExchange es la opción preferida para arbitraje COP/VES?
            </h2>
            <p className="text-gray-300 text-lg leading-relaxed mb-6">
              Monitoreamos cada oportunidad con nuestro motor de trading automatizado. Cuando detectamos spreads por
              encima de{' '}
              <span className="text-white font-semibold">
                {safePrices?.COP ? `${safePrices?.COP.spread.toFixed(2)}%` : 'el objetivo'}
              </span>{' '}
              en COP y{' '}
              <span className="text-white font-semibold">
                {safePrices?.VES ? `${safePrices?.VES.spread.toFixed(2)}%` : 'no disponible'}
              </span>{' '}
              en VES, emitimos alertas inmediatas y ejecutamos según tu configuración.
            </p>
            <ul className="space-y-4 text-gray-300">
              <li className="flex items-start gap-3">
                <CheckCircle className="h-6 w-6 text-primary-500 flex-shrink-0 mt-1" />
                <span>
                  <strong className="text-white">Operaciones verificadas:</strong> {safeStats?.total_trades || 0} trades
                  gestionados con un éxito del {safeStats?.success_rate ? safeStats.success_rate.toFixed(1) : '0'}%.
                </span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle className="h-6 w-6 text-primary-500 flex-shrink-0 mt-1" />
                <span>
                  <strong className="text-white">Ganancia neta real:</strong> USD{' '}
                  {safeStats?.total_profit ? safeStats.total_profit.toFixed(2) : '0.00'} en la última semana.
                </span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle className="h-6 w-6 text-primary-500 flex-shrink-0 mt-1" />
                <span>
                  <strong className="text-white">Soporte directo:</strong> contacto por WhatsApp y dashboard en vivo
                  para seguir cada movimiento.
                </span>
              </li>
            </ul>
          </div>

          <div className="bg-gray-800/60 border border-gray-700 rounded-2xl p-8 space-y-6">
            <h3 className="text-2xl font-bold text-white">Checklist para iniciar hoy</h3>
            <div className="space-y-4 text-gray-300">
              <div className="flex items-start gap-3">
                <Zap className="h-6 w-6 text-yellow-400 flex-shrink-0 mt-1" />
                <span>Configura tus claves de Binance P2P y define el monto diario máximo.</span>
              </div>
              <div className="flex items-start gap-3">
                <Shield className="h-6 w-6 text-blue-400 flex-shrink-0 mt-1" />
                <span>Activa las alertas automáticas para recibir notificaciones de oportunidades.</span>
              </div>
              <div className="flex items-start gap-3">
                <TrendingUp className="h-6 w-6 text-primary-500 flex-shrink-0 mt-1" />
                <span>Revisa el dashboard para confirmar el rendimiento por moneda y spread actual.</span>
              </div>
            </div>
            {whatsappLink && (
              <a
                href={whatsappLink}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-all"
              >
                <MessageCircle className="h-5 w-5" />
                Quiero activar mi cuenta
              </a>
            )}
          </div>
        </div>
      </section>

      {whatsappLink && (
        <WhatsAppButton phoneNumber={sanitizedPhone} message={whatsappMessage} />
      )}
    </div>
  )
}
