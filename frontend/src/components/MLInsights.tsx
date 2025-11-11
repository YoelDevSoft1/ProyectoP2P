'use client'

import { FormEvent, useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  Brain,
  Clock,
  Zap,
  Activity,
  Gauge,
  RefreshCw,
  ShieldCheck,
  Info,
  Play,
  CheckCircle,
  XCircle,
  Loader,
} from 'lucide-react'
import api from '@/lib/api'

type SpreadPrediction = {
  success: boolean
  error?: string
  current_spread?: number
  predicted_spread?: number
  spread_change?: number
  spread_change_percentage?: number
  confidence?: number
  horizon_minutes?: number
  recommendation?: string
  timestamp?: string
}

type TimingPrediction = {
  success: boolean
  error?: string
  current_hour_utc?: number
  best_timing?: {
    hour_offset: number
    hour_utc: number
    score: number
    recommendation: string
  }
  all_timings?: Array<{
    hour_offset: number
    hour_utc: number
    score: number
    recommendation: string
  }>
  recommendation?: string
  timestamp?: string
}

type ClassificationResult = {
  success: boolean
  classification?: string
  confidence?: number
  recommendation?: string
  probabilities?: Record<string, number>
  method?: string
  error?: string
  timestamp?: string
}

const assets = ['USDT', 'BTC', 'ETH'] as const
const fiats = ['COP', 'VES'] as const
const defaultClassificationInput = {
  roi: 3.2,
  spread: 1.5,
  liquidity: 5000,
  volatility: 0.85,
  market_quality_score: 72,
  estimated_execution_time: 3,
  estimated_slippage: 0.2,
  volume_ratio: 1.1,
}

type ClassificationKey = keyof typeof defaultClassificationInput

const classificationFields: Array<{
  key: ClassificationKey
  label: string
  min: number
  max: number
  step: number
}> = [
  { key: 'roi', label: 'ROI (%)', min: -10, max: 15, step: 0.1 },
  { key: 'spread', label: 'Spread (%)', min: 0, max: 10, step: 0.1 },
  { key: 'liquidity', label: 'Liquidez (USD)', min: 0, max: 100000, step: 100 },
  { key: 'volatility', label: 'Volatilidad', min: 0, max: 2, step: 0.05 },
  { key: 'market_quality_score', label: 'Calidad de mercado', min: 0, max: 100, step: 1 },
  { key: 'estimated_execution_time', label: 'Tiempo ejecución (min)', min: 1, max: 20, step: 1 },
  { key: 'estimated_slippage', label: 'Slippage estimado (%)', min: 0, max: 5, step: 0.1 },
  { key: 'volume_ratio', label: 'Volumen ratio', min: 0.1, max: 3, step: 0.05 },
]

export function MLInsights() {
  const [spreadParams, setSpreadParams] = useState({
    asset: 'USDT',
    fiat: 'COP',
    horizon: 15,
  })

  const [timingParams, setTimingParams] = useState({
    asset: 'USDT',
    fiat: 'COP',
  })

  const [classificationInput, setClassificationInput] = useState<typeof defaultClassificationInput>(
    defaultClassificationInput
  )

  const {
    data: spreadPrediction,
    isFetching: spreadLoading,
    refetch: refetchSpread,
  } = useQuery<SpreadPrediction>({
    queryKey: ['ml-spread', spreadParams.asset, spreadParams.fiat, spreadParams.horizon],
    queryFn: () => api.predictSpread(spreadParams.asset, spreadParams.fiat, spreadParams.horizon),
    refetchInterval: 60_000,
  })

  const {
    data: timingPrediction,
    isFetching: timingLoading,
    refetch: refetchTiming,
  } = useQuery<TimingPrediction>({
    queryKey: ['ml-timing', timingParams.asset, timingParams.fiat],
    queryFn: () => api.predictOptimalTiming(timingParams.asset, timingParams.fiat),
    refetchInterval: 90_000,
  })

  const classifyOpportunity = useMutation<ClassificationResult, Error, typeof classificationInput>({
    mutationFn: (payload) => api.classifyOpportunity(payload),
  })

  // Training mutations
  const trainMLSpreadPredictor = useMutation({
    mutationFn: () => api.trainMLSpreadPredictor(),
    onSuccess: () => {
      // Refetch spread prediction after training
      refetchSpread()
    },
  })

  const trainDLSpreadPredictor = useMutation({
    mutationFn: ({ epochs, batchSize, learningRate }: { epochs: number; batchSize: number; learningRate: number }) =>
      api.trainSpreadPredictor(epochs, batchSize, learningRate),
    onSuccess: () => {
      // Optionally refetch if needed
      refetchSpread()
    },
  })

  const [trainingParams, setTrainingParams] = useState({
    epochs: 50,
    batchSize: 32,
    learningRate: 0.001,
  })

  const handleClassificationSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    classifyOpportunity.mutate(classificationInput)
  }

  const classificationProbabilities = useMemo(() => {
    if (!classifyOpportunity.data?.probabilities) return []
    return Object.entries(classifyOpportunity.data.probabilities).sort((a, b) => b[1] - a[1])
  }, [classifyOpportunity.data?.probabilities])

  const spreadChangePct = spreadPrediction?.spread_change_percentage ?? 0
  const spreadDelta = spreadPrediction?.spread_change ?? 0
  const spreadDirection = spreadDelta > 0 ? 'up' : spreadDelta < 0 ? 'down' : 'flat'

  const formatHour = (hour: number | undefined) => {
    if (hour === undefined) return '--:--'
    return `${hour.toString().padStart(2, '0')}:00`
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white flex items-center gap-3">
            <Brain className="h-8 w-8 text-primary-400" />
            Inteligencia ML
          </h2>
          <p className="text-gray-400">
            Predicciones automatizadas para spreads, timing óptimo y clasificación de oportunidades.
          </p>
        </div>
        <div className="flex items-center gap-3 text-sm text-gray-400">
          <ShieldCheck className="h-4 w-4" />
          <span>Modelos entrenados con históricos reales</span>
        </div>
      </div>

      {/* Spread Forecast */}
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 rounded-2xl p-6 space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-wide text-primary-400 font-semibold">
              Predicción de Spread
            </p>
            <h3 className="text-2xl font-bold text-white flex items-center gap-2">
              Forecast {spreadParams.asset}/{spreadParams.fiat}
              <span className="text-sm font-medium text-gray-400">
                ({spreadParams.horizon} min)
              </span>
            </h3>
          </div>
          <div className="flex flex-wrap gap-3">
            <select
              value={spreadParams.asset}
              onChange={(event) =>
                setSpreadParams((prev) => ({ ...prev, asset: event.target.value }))
              }
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {assets.map((asset) => (
                <option key={asset} value={asset}>
                  {asset}
                </option>
              ))}
            </select>
            <select
              value={spreadParams.fiat}
              onChange={(event) =>
                setSpreadParams((prev) => ({ ...prev, fiat: event.target.value as 'COP' | 'VES' }))
              }
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {fiats.map((fiat) => (
                <option key={fiat} value={fiat}>
                  {fiat}
                </option>
              ))}
            </select>
            <input
              type="number"
              min={5}
              max={120}
              step={5}
              value={spreadParams.horizon}
              onChange={(event) =>
                setSpreadParams((prev) => ({ ...prev, horizon: Number(event.target.value) }))
              }
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary-500 w-24"
              placeholder="Horizon"
            />
            <button
              onClick={() => refetchSpread()}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-500 transition disabled:opacity-50"
              disabled={spreadLoading}
            >
              <RefreshCw className={`h-4 w-4 ${spreadLoading ? 'animate-spin' : ''}`} />
              Actualizar
            </button>
          </div>
        </div>

        {spreadPrediction?.success ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-5 bg-gray-900/60 border border-gray-700 rounded-xl">
              <p className="text-sm text-gray-400 mb-1">Spread actual</p>
              <div className="flex items-end gap-2">
                <span className="text-3xl font-bold text-white">
                  {(spreadPrediction.current_spread ?? 0).toFixed(2)}%
                </span>
                <span className="text-xs text-gray-500">
                  Actualizado {spreadPrediction.timestamp ? new Date(spreadPrediction.timestamp).toLocaleTimeString() : ''}
                </span>
              </div>
            </div>
            <div className="p-5 bg-gray-900/60 border border-gray-700 rounded-xl">
              <p className="text-sm text-gray-400 mb-1">Spread proyectado</p>
              <div className="flex items-end gap-2">
                <span className="text-3xl font-bold text-primary-300">
                  {(spreadPrediction.predicted_spread ?? 0).toFixed(2)}%
                </span>
                <span
                  className={`text-sm font-semibold ${
                    spreadDirection === 'up'
                      ? 'text-red-400'
                      : spreadDirection === 'down'
                      ? 'text-green-400'
                      : 'text-gray-400'
                  }`}
                >
                  {spreadDirection === 'up' ? '+' : ''}
                  {spreadChangePct.toFixed(2)}%
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-1">
                Cambio esperado en {spreadPrediction.horizon_minutes} minutos
              </p>
            </div>
            <div className="p-5 bg-gray-900/60 border border-gray-700 rounded-xl">
              <p className="text-sm text-gray-400 mb-1">Confianza</p>
              <div className="flex items-center gap-3">
                <Gauge className="h-10 w-10 text-primary-400" />
                <div>
                  <p className="text-3xl font-bold text-white">
                    {Math.round((spreadPrediction.confidence ?? 0) * 100)}%
                  </p>
                  <p className="text-xs text-gray-400">Modelo Gradient Boosting</p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-xl text-red-300 space-y-4">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold">Modelo no entrenado todavía</p>
                <p className="text-sm mt-1">
                  Entrena un modelo para habilitar las predicciones de spread.
                </p>
              </div>
            </div>
            
            {/* Training Buttons */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
              {/* ML Training (Gradient Boosting) */}
              <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <p className="text-sm font-semibold text-white">Machine Learning</p>
                    <p className="text-xs text-gray-400">Gradient Boosting</p>
                  </div>
                  {trainMLSpreadPredictor.isSuccess && (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  )}
                  {trainMLSpreadPredictor.isError && (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                  {trainMLSpreadPredictor.isPending && (
                    <Loader className="h-5 w-5 text-primary-400 animate-spin" />
                  )}
                </div>
                <button
                  onClick={() => trainMLSpreadPredictor.mutate()}
                  disabled={trainMLSpreadPredictor.isPending}
                  className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Play className="h-4 w-4" />
                  {trainMLSpreadPredictor.isPending ? 'Entrenando...' : 'Entrenar ML Model'}
                </button>
                {trainMLSpreadPredictor.isSuccess && (
                  <p className="text-xs text-green-400 mt-2">
                    ✅ Modelo entrenado exitosamente
                  </p>
                )}
                {trainMLSpreadPredictor.isError && (
                  <p className="text-xs text-red-400 mt-2">
                    ❌ Error: {trainMLSpreadPredictor.error?.message || 'Error desconocido'}
                  </p>
                )}
              </div>

              {/* DL Training (GRU) */}
              <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <p className="text-sm font-semibold text-white">Deep Learning</p>
                    <p className="text-xs text-gray-400">GRU Model</p>
                  </div>
                  {trainDLSpreadPredictor.isSuccess && (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  )}
                  {trainDLSpreadPredictor.isError && (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                  {trainDLSpreadPredictor.isPending && (
                    <Loader className="h-5 w-5 text-primary-400 animate-spin" />
                  )}
                </div>
                <div className="space-y-2">
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <label className="text-gray-400 block mb-1">Épocas</label>
                      <input
                        type="number"
                        min="1"
                        max="500"
                        value={trainingParams.epochs}
                        onChange={(e) =>
                          setTrainingParams((prev) => ({
                            ...prev,
                            epochs: parseInt(e.target.value) || 50,
                          }))
                        }
                        className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-white text-xs"
                        disabled={trainDLSpreadPredictor.isPending}
                      />
                    </div>
                    <div>
                      <label className="text-gray-400 block mb-1">Batch Size</label>
                      <input
                        type="number"
                        min="1"
                        max="256"
                        value={trainingParams.batchSize}
                        onChange={(e) =>
                          setTrainingParams((prev) => ({
                            ...prev,
                            batchSize: parseInt(e.target.value) || 32,
                          }))
                        }
                        className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-white text-xs"
                        disabled={trainDLSpreadPredictor.isPending}
                      />
                    </div>
                    <div>
                      <label className="text-gray-400 block mb-1">LR</label>
                      <input
                        type="number"
                        min="0.0001"
                        max="0.1"
                        step="0.0001"
                        value={trainingParams.learningRate}
                        onChange={(e) =>
                          setTrainingParams((prev) => ({
                            ...prev,
                            learningRate: parseFloat(e.target.value) || 0.001,
                          }))
                        }
                        className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-white text-xs"
                        disabled={trainDLSpreadPredictor.isPending}
                      />
                    </div>
                  </div>
                  <button
                    onClick={() =>
                      trainDLSpreadPredictor.mutate({
                        epochs: trainingParams.epochs,
                        batchSize: trainingParams.batchSize,
                        learningRate: trainingParams.learningRate,
                      })
                    }
                    disabled={trainDLSpreadPredictor.isPending}
                    className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-purple-600 text-white text-sm font-medium hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Brain className="h-4 w-4" />
                    {trainDLSpreadPredictor.isPending ? 'Entrenando...' : 'Entrenar GRU Model'}
                  </button>
                  {trainDLSpreadPredictor.isSuccess && (
                    <div className="text-xs text-green-400 mt-2 space-y-1">
                      <p>✅ Modelo GRU entrenado exitosamente</p>
                      {trainDLSpreadPredictor.data?.test_loss !== undefined && (
                        <p>Test Loss: {typeof trainDLSpreadPredictor.data.test_loss === 'number' ? trainDLSpreadPredictor.data.test_loss.toFixed(4) : 'N/A'}</p>
                      )}
                    </div>
                  )}
                  {trainDLSpreadPredictor.isError && (
                    <p className="text-xs text-red-400 mt-2">
                      ❌ Error: {trainDLSpreadPredictor.error?.message || 'Error desconocido'}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {spreadPrediction?.recommendation && spreadPrediction.success && (
          <div className="p-4 bg-primary-500/10 border border-primary-500/40 rounded-xl flex items-start gap-3">
            <Zap className="h-5 w-5 text-primary-300 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm uppercase tracking-wide text-primary-300 font-semibold">Recomendación ML</p>
              <p className="text-white">{spreadPrediction.recommendation}</p>
            </div>
          </div>
        )}
      </div>

      {/* Timing + Classification grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Timing */}
        <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 rounded-2xl p-6 space-y-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm uppercase tracking-wide text-primary-400 font-semibold">
                Timing Óptimo
              </p>
              <h3 className="text-2xl font-bold text-white flex items-center gap-2">
                Horario recomendado
                <Clock className="h-6 w-6 text-primary-300" />
              </h3>
            </div>
            <div className="flex gap-3">
              <select
                value={timingParams.asset}
                onChange={(event) =>
                  setTimingParams((prev) => ({ ...prev, asset: event.target.value }))
                }
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-primary-500"
              >
                {assets.map((asset) => (
                  <option key={asset} value={asset}>
                    {asset}
                  </option>
                ))}
              </select>
              <select
                value={timingParams.fiat}
                onChange={(event) =>
                  setTimingParams((prev) => ({ ...prev, fiat: event.target.value as 'COP' | 'VES' }))
                }
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-primary-500"
              >
                {fiats.map((fiat) => (
                  <option key={fiat} value={fiat}>
                    {fiat}
                  </option>
                ))}
              </select>
              <button
                onClick={() => refetchTiming()}
                className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-700 text-white text-sm font-medium hover:bg-gray-600 transition disabled:opacity-50"
                disabled={timingLoading}
              >
                <RefreshCw className={`h-4 w-4 ${timingLoading ? 'animate-spin' : ''}`} />
                Actualizar
              </button>
            </div>
          </div>

          {timingPrediction?.success ? (
            <>
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm text-gray-400 mb-1">Mejor ventana (UTC)</p>
                  <p className="text-4xl font-bold text-primary-300">
                    {formatHour(timingPrediction.best_timing?.hour_utc)}
                  </p>
                  <p className="text-sm text-gray-400">
                    En {timingPrediction.best_timing?.hour_offset ?? 0} horas
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-primary-500/10 border border-primary-500/30">
                  <p className="text-sm text-primary-300 font-semibold">Recomendación</p>
                  <p className="text-white">{timingPrediction.recommendation}</p>
                </div>
              </div>

              <div className="overflow-hidden rounded-xl border border-gray-700">
                <table className="min-w-full divide-y divide-gray-700 text-sm">
                  <thead className="bg-gray-900">
                    <tr>
                      <th className="px-4 py-2 text-left text-gray-400 font-semibold">Hora (UTC)</th>
                      <th className="px-4 py-2 text-left text-gray-400 font-semibold">En</th>
                      <th className="px-4 py-2 text-left text-gray-400 font-semibold">Score</th>
                      <th className="px-4 py-2 text-left text-gray-400 font-semibold">Estado</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {timingPrediction.all_timings?.map((timing) => (
                      <tr key={timing.hour_offset} className="hover:bg-gray-900/60">
                        <td className="px-4 py-2 text-white font-medium">
                          {formatHour(timing.hour_utc)}
                        </td>
                        <td className="px-4 py-2 text-gray-400">{timing.hour_offset}h</td>
                        <td className="px-4 py-2 text-white">{timing.score.toFixed(1)}</td>
                        <td className="px-4 py-2">
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-semibold ${
                              timing.recommendation === 'OPTIMAL'
                                ? 'bg-green-500/20 text-green-300'
                                : timing.recommendation === 'GOOD'
                                ? 'bg-yellow-500/20 text-yellow-300'
                                : 'bg-red-500/20 text-red-300'
                            }`}
                          >
                            {timing.recommendation}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="p-4 bg-yellow-500/10 border border-yellow-500/40 rounded-xl text-yellow-200 flex items-center gap-3">
              <Info className="h-5 w-5" />
              <p>No hay datos suficientes para calcular el timing óptimo.</p>
            </div>
          )}
        </div>

        {/* Classification */}
        <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 rounded-2xl p-6 space-y-5">
          <div>
            <p className="text-sm uppercase tracking-wide text-primary-400 font-semibold">
              Clasificación de Oportunidades
            </p>
            <h3 className="text-2xl font-bold text-white flex items-center gap-2">
              Evaluador ML
              <Activity className="h-6 w-6 text-primary-300" />
            </h3>
            <p className="text-sm text-gray-400 mt-1">
              Ajusta los parámetros y deja que el modelo determine si vale la pena ejecutar.
            </p>
          </div>

          <form className="space-y-4" onSubmit={handleClassificationSubmit}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {classificationFields.map((field) => (
                <label key={field.key} className="text-sm font-medium text-gray-300 space-y-1">
                  <span>{field.label}</span>
                  <input
                    type="number"
                    step={field.step}
                    min={field.min}
                    max={field.max}
                    value={classificationInput[field.key]}
                    onChange={(event) =>
                      setClassificationInput((prev) => ({
                        ...prev,
                        [field.key]: Number(event.target.value),
                      }))
                    }
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-primary-500"
                  />
                </label>
              ))}
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                type="submit"
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-500 rounded-lg text-white font-semibold transition disabled:opacity-50"
                disabled={classifyOpportunity.isPending}
              >
                <Brain className="h-4 w-4" />
                Ejecutar Clasificación
              </button>
              {classifyOpportunity.data && (
                <button
                  type="button"
                  onClick={() => classifyOpportunity.reset()}
                  className="px-4 py-2 border border-gray-600 rounded-lg text-gray-300 hover:bg-gray-800 transition"
                >
                  Limpiar resultado
                </button>
              )}
            </div>
          </form>

          {classifyOpportunity.isPending && (
            <div className="p-4 bg-gray-900 border border-gray-700 rounded-xl text-gray-300">
              Procesando oportunidad...
            </div>
          )}

          {classifyOpportunity.data && classifyOpportunity.data.success && (
            <div className="space-y-4">
              <div className="p-5 bg-gray-900 border border-gray-700 rounded-xl flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-400">Clasificación ML</p>
                  <p className="text-3xl font-bold text-white">
                    {classifyOpportunity.data.classification}
                  </p>
                  <p className="text-sm text-gray-500">
                    Confianza: {Math.round((classifyOpportunity.data.confidence ?? 0) * 100)}%
                  </p>
                </div>
                {classifyOpportunity.data.recommendation && (
                  <div className="p-4 bg-primary-500/10 border border-primary-500/30 rounded-lg">
                    <p className="text-sm text-primary-300 font-semibold">Recomendación</p>
                    <p className="text-white">{classifyOpportunity.data.recommendation}</p>
                  </div>
                )}
              </div>

              {classificationProbabilities.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-gray-300">Distribución de probabilidades</p>
                  <div className="space-y-2">
                    {classificationProbabilities.map(([label, value]) => (
                      <div key={label}>
                        <div className="flex justify-between text-xs text-gray-400">
                          <span>{label}</span>
                          <span>{Math.round(value * 100)}%</span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-gray-800">
                          <div
                            className={`h-2 rounded-full ${
                              label === classifyOpportunity.data?.classification
                                ? 'bg-primary-500'
                                : 'bg-gray-600'
                            }`}
                            style={{ width: `${Math.min(100, Math.round(value * 100))}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {classifyOpportunity.data && !classifyOpportunity.data.success && (
            <div className="p-4 bg-red-500/10 border border-red-500/40 rounded-xl text-red-300">
              {classifyOpportunity.data.error || 'No se pudo clasificar la oportunidad.'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
