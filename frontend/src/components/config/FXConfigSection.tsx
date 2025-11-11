'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, AlertCircle, CheckCircle, X } from 'lucide-react'
import api from '@/lib/api'
import type { FXConfig, ConfigUpdateRequest } from '@/types/config'

interface FXConfigSectionProps {
  config: FXConfig
  onConfigChange: () => void
}

export function FXConfigSection({ config, onConfigChange }: FXConfigSectionProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<FXConfig>(config)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle')
  const [saveMessage, setSaveMessage] = useState<string>('')
  const [newFallbackCurrency, setNewFallbackCurrency] = useState<string>('')
  const [newFallbackRate, setNewFallbackRate] = useState<string>('')

  const updateMutation = useMutation({
    mutationFn: (data: ConfigUpdateRequest) => api.updateConfiguration(data),
    onSuccess: () => {
      setSaveStatus('success')
      setSaveMessage('Configuración guardada exitosamente')
      queryClient.invalidateQueries({ queryKey: ['configuration'] })
      setTimeout(() => {
        setSaveStatus('idle')
        setSaveMessage('')
      }, 3000)
    },
    onError: (error: any) => {
      setSaveStatus('error')
      setSaveMessage(error.response?.data?.detail || 'Error al guardar la configuración')
      setTimeout(() => {
        setSaveStatus('idle')
        setSaveMessage('')
      }, 5000)
    },
  })

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (formData.cache_ttl_seconds < 60 || formData.cache_ttl_seconds > 3600) {
      newErrors.cache_ttl_seconds = 'El TTL debe estar entre 60 y 3600 segundos'
    }
    if (formData.trm_update_interval < 60 || formData.trm_update_interval > 3600) {
      newErrors.trm_update_interval = 'El intervalo debe estar entre 60 y 3600 segundos'
    }
    if (formData.ves_update_interval < 60 || formData.ves_update_interval > 3600) {
      newErrors.ves_update_interval = 'El intervalo debe estar entre 60 y 3600 segundos'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSave = () => {
    if (!validate()) {
      setSaveStatus('error')
      setSaveMessage('Por favor corrige los errores antes de guardar')
      return
    }

    setSaveStatus('saving')
    updateMutation.mutate({
      fx: formData,
    })
  }

  const handleChange = (field: keyof FXConfig, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    onConfigChange()
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }

  const addFallbackRate = () => {
    if (newFallbackCurrency.trim() && newFallbackRate.trim()) {
      const rate = parseFloat(newFallbackRate)
      if (!isNaN(rate) && rate > 0) {
        handleChange('fallback_rates', {
          ...formData.fallback_rates,
          [newFallbackCurrency.trim().toUpperCase()]: rate,
        })
        setNewFallbackCurrency('')
        setNewFallbackRate('')
      }
    }
  }

  const removeFallbackRate = (currency: string) => {
    const newRates = { ...formData.fallback_rates }
    delete newRates[currency]
    handleChange('fallback_rates', newRates)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Configuración FX y Tasas</h2>
          <p className="text-gray-400 text-sm mt-1">
            Configura las tasas de cambio, caché e intervalos de actualización
          </p>
        </div>
        <button
          onClick={handleSave}
          disabled={updateMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Save className="h-4 w-4" />
          {updateMutation.isPending ? 'Guardando...' : 'Guardar Cambios'}
        </button>
      </div>

      {saveStatus !== 'idle' && (
        <div
          className={`
            flex items-center gap-2 p-4 rounded-lg
            ${saveStatus === 'success' ? 'bg-green-900/30 border border-green-500/50 text-green-400' : ''}
            ${saveStatus === 'error' ? 'bg-red-900/30 border border-red-500/50 text-red-400' : ''}
          `}
        >
          {saveStatus === 'success' ? (
            <CheckCircle className="h-5 w-5" />
          ) : (
            <AlertCircle className="h-5 w-5" />
          )}
          <span>{saveMessage}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Cache TTL */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            TTL de Caché (segundos)
          </label>
          <input
            type="number"
            min="60"
            max="3600"
            value={formData.cache_ttl_seconds}
            onChange={(e) => handleChange('cache_ttl_seconds', parseInt(e.target.value) || 60)}
            className={`w-full bg-gray-700 border ${
              errors.cache_ttl_seconds ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.cache_ttl_seconds && (
            <p className="text-xs text-red-400 mt-1">{errors.cache_ttl_seconds}</p>
          )}
        </div>

        {/* TRM Update Interval */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Intervalo TRM (segundos)
          </label>
          <input
            type="number"
            min="60"
            max="3600"
            value={formData.trm_update_interval}
            onChange={(e) => handleChange('trm_update_interval', parseInt(e.target.value) || 60)}
            className={`w-full bg-gray-700 border ${
              errors.trm_update_interval ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.trm_update_interval && (
            <p className="text-xs text-red-400 mt-1">{errors.trm_update_interval}</p>
          )}
        </div>

        {/* VES Update Interval */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Intervalo VES (segundos)
          </label>
          <input
            type="number"
            min="60"
            max="3600"
            value={formData.ves_update_interval}
            onChange={(e) => handleChange('ves_update_interval', parseInt(e.target.value) || 60)}
            className={`w-full bg-gray-700 border ${
              errors.ves_update_interval ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.ves_update_interval && (
            <p className="text-xs text-red-400 mt-1">{errors.ves_update_interval}</p>
          )}
        </div>

        {/* Fallback Rates */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Tasas de Respaldo
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={newFallbackCurrency}
              onChange={(e) => setNewFallbackCurrency(e.target.value)}
              placeholder="Moneda (ej: COP)"
              className="flex-1 bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <input
              type="number"
              step="0.01"
              value={newFallbackRate}
              onChange={(e) => setNewFallbackRate(e.target.value)}
              placeholder="Tasa"
              className="flex-1 bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <button
              onClick={addFallbackRate}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
            >
              Agregar
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(formData.fallback_rates).map(([currency, rate]) => (
              <span
                key={currency}
                className="inline-flex items-center gap-2 px-3 py-1 bg-gray-700 text-white rounded-lg"
              >
                {currency}: {rate.toFixed(2)}
                <button
                  onClick={() => removeFallbackRate(currency)}
                  className="text-gray-400 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

