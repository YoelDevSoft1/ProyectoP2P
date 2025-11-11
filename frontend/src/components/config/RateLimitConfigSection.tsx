'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, AlertCircle, CheckCircle } from 'lucide-react'
import api from '@/lib/api'
import type { RateLimitConfig, ConfigUpdateRequest } from '@/types/config'

interface RateLimitConfigSectionProps {
  config: RateLimitConfig
  onConfigChange: () => void
}

export function RateLimitConfigSection({ config, onConfigChange }: RateLimitConfigSectionProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<RateLimitConfig>(config)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle')
  const [saveMessage, setSaveMessage] = useState<string>('')

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

    if (formData.rate_limit_per_minute < 1 || formData.rate_limit_per_minute > 1000) {
      newErrors.rate_limit_per_minute = 'El límite debe estar entre 1 y 1000 por minuto'
    }
    if (formData.rate_limit_binance_api < 1 || formData.rate_limit_binance_api > 10000) {
      newErrors.rate_limit_binance_api = 'El límite debe estar entre 1 y 10000'
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
      rate_limiting: formData,
    })
  }

  const handleChange = (field: keyof RateLimitConfig, value: any) => {
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Configuración de Rate Limiting</h2>
          <p className="text-gray-400 text-sm mt-1">
            Configura los límites de tasa para API y Binance
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
        {/* Rate Limit Per Minute */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Límite de Tasa por Minuto
          </label>
          <input
            type="number"
            min="1"
            max="1000"
            value={formData.rate_limit_per_minute}
            onChange={(e) => handleChange('rate_limit_per_minute', parseInt(e.target.value) || 1)}
            className={`w-full bg-gray-700 border ${
              errors.rate_limit_per_minute ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.rate_limit_per_minute && (
            <p className="text-xs text-red-400 mt-1">{errors.rate_limit_per_minute}</p>
          )}
          <p className="text-xs text-gray-500 mt-1">Rango: 1 - 1000 por minuto</p>
        </div>

        {/* Rate Limit Binance API */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Límite de Tasa Binance API
          </label>
          <input
            type="number"
            min="1"
            max="10000"
            value={formData.rate_limit_binance_api}
            onChange={(e) => handleChange('rate_limit_binance_api', parseInt(e.target.value) || 1)}
            className={`w-full bg-gray-700 border ${
              errors.rate_limit_binance_api ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.rate_limit_binance_api && (
            <p className="text-xs text-red-400 mt-1">{errors.rate_limit_binance_api}</p>
          )}
          <p className="text-xs text-gray-500 mt-1">Rango: 1 - 10000</p>
        </div>
      </div>
    </div>
  )
}

