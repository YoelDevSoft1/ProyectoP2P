'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { createChart, IChartApi, ISeriesApi, ColorType, Time, CandlestickData } from 'lightweight-charts'
import { TrendingUp, TrendingDown, BarChart3, Activity, Clock } from 'lucide-react'
import api from '@/lib/api'

interface ForexTradingChartProps {
  pair: string
  timeframe?: string
  height?: number
}

type Timeframe = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d'

const TIMEFRAMES: { value: Timeframe; label: string }[] = [
  { value: '1m', label: '1m' },
  { value: '5m', label: '5m' },
  { value: '15m', label: '15m' },
  { value: '30m', label: '30m' },
  { value: '1h', label: '1H' },
  { value: '4h', label: '4H' },
  { value: '1d', label: '1D' },
]

export function ForexTradingChart({ pair, timeframe = '1h', height = 500 }: ForexTradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const volumeContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const volumeChartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null)
  const [selectedTimeframe, setSelectedTimeframe] = useState<Timeframe>(timeframe as Timeframe)
  const [currentPrice, setCurrentPrice] = useState<number | null>(null)
  const [priceChange, setPriceChange] = useState<{ value: number; percent: number } | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Generar datos simulados de velas (OHLCV)
  const generateCandleData = useCallback((basePrice: number, count: number = 200) => {
    const data: CandlestickData[] = []
    let price = basePrice
    const now = Math.floor(Date.now() / 1000)
    const intervalSeconds = getTimeframeSeconds(selectedTimeframe)

    for (let i = count; i >= 0; i--) {
      const time = (now - i * intervalSeconds) as Time
      const open = price
      const volatility = basePrice * 0.001 // 0.1% de volatilidad
      const change = (Math.random() - 0.5) * volatility * 2
      const high = open + Math.abs(change) * (0.5 + Math.random() * 0.5)
      const low = open - Math.abs(change) * (0.5 + Math.random() * 0.5)
      const close = open + change

      data.push({
        time,
        open: Number(open.toFixed(5)),
        high: Number(high.toFixed(5)),
        low: Number(low.toFixed(5)),
        close: Number(close.toFixed(5)),
      })

      price = close
    }

    return data
  }, [selectedTimeframe])

  const getTimeframeSeconds = (tf: Timeframe): number => {
    const map: Record<Timeframe, number> = {
      '1m': 60,
      '5m': 300,
      '15m': 900,
      '30m': 1800,
      '1h': 3600,
      '4h': 14400,
      '1d': 86400,
    }
    return map[tf]
  }

  // Inicializar gráfico principal (velas)
  useEffect(() => {
    if (!chartContainerRef.current) return

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#1a1a1a' },
        textColor: '#d1d5db',
        fontSize: 12,
      },
      grid: {
        vertLines: {
          color: '#2a2a2a',
          style: 1,
        },
        horzLines: {
          color: '#2a2a2a',
          style: 1,
        },
      },
      width: chartContainerRef.current.clientWidth,
      height: height - 120, // Dejar espacio para el volumen
      timeScale: {
        timeVisible: true,
        secondsVisible: selectedTimeframe === '1m' || selectedTimeframe === '5m',
        borderColor: '#3a3a3a',
      },
      rightPriceScale: {
        borderColor: '#3a3a3a',
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      leftPriceScale: {
        visible: false,
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: '#6b7280',
          width: 1,
          style: 3,
        },
        horzLine: {
          color: '#6b7280',
          width: 1,
          style: 3,
        },
      },
    })

    // Serie de velas
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
      priceFormat: {
        type: 'price',
        precision: 5,
        minMove: 0.00001,
      },
    })

    chartRef.current = chart
    candlestickSeriesRef.current = candlestickSeries

    // Manejar resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        })
      }
      if (volumeContainerRef.current && volumeChartRef.current) {
        try {
          volumeChartRef.current.applyOptions({
            width: volumeContainerRef.current.clientWidth,
          })
        } catch (e) {
          // Ignorar errores si el gráfico fue eliminado
        }
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (chartRef.current) {
        chartRef.current.remove()
        chartRef.current = null
      }
    }
  }, [height])

  // Inicializar gráfico de volumen (separado)
  useEffect(() => {
    if (!volumeContainerRef.current) return

    const volumeChart = createChart(volumeContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#1a1a1a' },
        textColor: '#9ca3af',
        fontSize: 11,
      },
      grid: {
        vertLines: {
          visible: false,
        },
        horzLines: {
          color: '#2a2a2a',
          style: 1,
        },
      },
      width: volumeContainerRef.current.clientWidth,
      height: 100,
      timeScale: {
        visible: false, // Ocultar escala de tiempo en volumen (se sincroniza con el principal)
        borderColor: '#3a3a3a',
      },
      rightPriceScale: {
        visible: false,
      },
      leftPriceScale: {
        visible: false,
      },
      crosshair: {
        mode: 0, // Solo línea vertical
        vertLine: {
          color: '#6b7280',
          width: 1,
          style: 3,
        },
        horzLine: {
          visible: false,
        },
      },
    })

    // Sincronizar escalas de tiempo (solo si el gráfico principal existe)
    if (chartRef.current) {
      try {
        volumeChart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {
          if (chartRef.current && timeRange) {
            try {
              chartRef.current.timeScale().setVisibleRange(timeRange)
            } catch (e) {
              // Ignorar errores de sincronización
            }
          }
        })
      } catch (e) {
        // Ignorar errores de suscripción
      }
    }

    const volumeSeries = volumeChart.addHistogramSeries({
      color: '#26a69a40',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
      scaleMargins: {
        top: 0.1,
        bottom: 0.1,
      },
    })

    volumeChartRef.current = volumeChart
    volumeSeriesRef.current = volumeSeries

    return () => {
      if (volumeChartRef.current) {
        try {
          volumeChartRef.current.remove()
        } catch (e) {
          // Ignorar errores si ya fue eliminado
        }
        volumeChartRef.current = null
      }
    }
  }, [])

  // Cargar y actualizar datos
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true)
      try {
        // Obtener precio actual
        const [base, quote] = pair.split('/')
        const rate = await api.analyzeForexPair(pair, 'daily')
        
        let basePrice = 1.0850 // Precio por defecto
        if (rate?.ANÁLISIS_FOREX?.DATOS_ACTUALES?.['Precio Actual']) {
          basePrice = rate.ANÁLISIS_FOREX.DATOS_ACTUALES['Precio Actual']
        } else {
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
          }
          basePrice = basePrices[pair] || basePrice
        }

        setCurrentPrice(basePrice)

        // Generar datos de velas
        const candleData = generateCandleData(basePrice, 200)
        const volumeData = candleData.map((candle) => ({
          time: candle.time,
          value: Math.random() * 1000000 + 500000,
          color: candle.close >= candle.open ? '#26a69a60' : '#ef535060',
        }))

        // Calcular cambio de precio
        if (candleData.length > 1) {
          const first = candleData[0].close
          const last = candleData[candleData.length - 1].close
          const change = last - first
          const percent = (change / first) * 100
          setPriceChange({ value: change, percent })
        }

        // Actualizar series
        if (candlestickSeriesRef.current) {
          candlestickSeriesRef.current.setData(candleData)
        }
        if (volumeSeriesRef.current) {
          volumeSeriesRef.current.setData(volumeData)
        }

        // Sincronizar escalas de tiempo
        if (chartRef.current && volumeChartRef.current) {
          try {
            const timeRange = chartRef.current.timeScale().getVisibleRange()
            if (timeRange) {
              volumeChartRef.current.timeScale().setVisibleRange(timeRange)
            }
            // Auto-scroll al final
            if (candleData.length > 0) {
              chartRef.current.timeScale().scrollToPosition(-1, false)
              volumeChartRef.current.timeScale().scrollToPosition(-1, false)
            }
          } catch (e) {
            // Ignorar errores si los gráficos fueron eliminados
            console.warn('Error syncing charts:', e)
          }
        }
      } catch (error) {
        console.error('Error loading chart data:', error)
        // Usar datos simulados como fallback
        const basePrice = 1.0850
        const candleData = generateCandleData(basePrice, 200)
        if (candlestickSeriesRef.current) {
          candlestickSeriesRef.current.setData(candleData)
        }
        setCurrentPrice(basePrice)
      } finally {
        setIsLoading(false)
      }
    }

    if (chartRef.current && candlestickSeriesRef.current) {
      loadData()
    }
  }, [pair, selectedTimeframe, generateCandleData])

  // Actualizar precio en tiempo real (simulado)
  useEffect(() => {
    if (!currentPrice) return

    const interval = setInterval(() => {
      if (candlestickSeriesRef.current && chartRef.current) {
        const now = Math.floor(Date.now() / 1000) as Time
        const lastCandle = candlestickSeriesRef.current.data().slice(-1)[0]
        
        if (lastCandle) {
          const volatility = currentPrice * 0.0001
          const change = (Math.random() - 0.5) * volatility * 2
          const newClose = Number((lastCandle.close + change).toFixed(5))
          const newHigh = Math.max(lastCandle.high, newClose)
          const newLow = Math.min(lastCandle.low, newClose)

          candlestickSeriesRef.current.update({
            time: now,
            open: lastCandle.close,
            high: newHigh,
            low: newLow,
            close: newClose,
          })

          setCurrentPrice(newClose)
          
          // Actualizar cambio de precio
          if (priceChange) {
            const firstPrice = currentPrice - priceChange.value
            const newChange = newClose - firstPrice
            const newPercent = (newChange / firstPrice) * 100
            setPriceChange({ value: newChange, percent: newPercent })
          }
        }
      }
    }, 2000) // Actualizar cada 2 segundos

    return () => clearInterval(interval)
  }, [currentPrice, priceChange])

  const formatPrice = (price: number | null) => {
    if (price === null) return '--'
    return price.toLocaleString('en-US', {
      minimumFractionDigits: 5,
      maximumFractionDigits: 5,
    })
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl overflow-hidden">
      {/* Header del gráfico */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-xl font-bold text-white">{pair}</h3>
            <div className="flex items-center gap-4 mt-1">
              {currentPrice && (
                <span className="text-2xl font-bold text-white">{formatPrice(currentPrice)}</span>
              )}
              {priceChange && (
                <span
                  className={`text-lg font-semibold flex items-center gap-1 ${
                    priceChange.value >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {priceChange.value >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                  {priceChange.value >= 0 ? '+' : ''}
                  {priceChange.value.toFixed(5)} ({priceChange.percent >= 0 ? '+' : ''}
                  {priceChange.percent.toFixed(2)}%)
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf.value}
                onClick={() => setSelectedTimeframe(tf.value)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                  selectedTimeframe === tf.value
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {tf.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Gráfico principal (velas) */}
      <div className="relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80 z-10">
            <div className="flex flex-col items-center gap-2">
              <Activity className="h-6 w-6 text-primary-400 animate-spin" />
              <span className="text-gray-400 text-sm">Cargando datos...</span>
            </div>
          </div>
        )}
        <div ref={chartContainerRef} style={{ width: '100%', height: `${height - 120}px` }} />
      </div>

      {/* Gráfico de volumen (separado) */}
      <div className="border-t border-gray-700">
        <div className="px-4 py-2 bg-gray-800/50">
          <span className="text-xs text-gray-400 uppercase tracking-wide">Volumen</span>
        </div>
        <div ref={volumeContainerRef} style={{ width: '100%', height: '100px' }} />
      </div>

      {/* Indicadores técnicos */}
      <div className="bg-gray-800 border-t border-gray-700 p-3">
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-gray-400" />
            <span className="text-gray-400">Indicadores:</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-gray-300">RSI(14): 62.5</span>
            <span className="text-gray-300">MACD: Alcista</span>
            <span className="text-gray-300">Volumen: Alto</span>
          </div>
        </div>
      </div>
    </div>
  )
}
