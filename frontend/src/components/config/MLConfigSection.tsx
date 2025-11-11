'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, AlertCircle, CheckCircle } from 'lucide-react'
import api from '@/lib/api'
import type { MLConfig, ConfigUpdateRequest } from '@/types/config'

interface MLConfigSectionProps {
  config: MLConfig
  onConfigChange: () => void
}

export function MLConfigSection({ config, onConfigChange }: MLConfigSectionProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<MLConfig>(config)
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

    if (formData.retrain_interval < 3600) {
      newErrors.retrain_interval = 'El intervalo debe ser al menos 3600 segundos (1 hora)'
    }
    if (formData.min_data_points < 100) {
      newErrors.min_data_points = 'Debe haber al menos 100 puntos de datos'
    }
    if (formData.confidence_threshold < 0 || formData.confidence_threshold > 1) {
      newErrors.confidence_threshold = 'El umbral debe estar entre 0 y 1'
    }
    if (formData.spread_threshold < 0 || formData.spread_threshold > 10) {
      newErrors.spread_threshold = 'El umbral de spread debe estar entre 0 y 10%'
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
      ml: formData,
    })
  }

  const handleChange = (field: keyof MLConfig, value: any) => {
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
          <h2 className="text-2xl font-bold text-white">Configuración de Machine Learning</h2>
          <p className="text-gray-400 text-sm mt-1">
            Configura los parámetros de entrenamiento y predicción del modelo ML
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
        {/* Retrain Interval */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Intervalo de Reentrenamiento (segundos)
          </label>
          <input
            type="number"
            min="3600"
            value={formData.retrain_interval}
            onChange={(e) => handleChange('retrain_interval', parseInt(e.target.value) || 3600)}
            className={`w-full bg-gray-700 border ${
              errors.retrain_interval ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.retrain_interval && (
            <p className="text-xs text-red-400 mt-1">{errors.retrain_interval}</p>
          )}
          <p className="text-xs text-gray-500 mt-1">Mínimo: 3600 segundos (1 hora)</p>
        </div>

        {/* Min Data Points */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Puntos de Datos Mínimos
          </label>
          <input
            type="number"
            min="100"
            value={formData.min_data_points}
            onChange={(e) => handleChange('min_data_points', parseInt(e.target.value) || 100)}
            className={`w-full bg-gray-700 border ${
              errors.min_data_points ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.min_data_points && (
            <p className="text-xs text-red-400 mt-1">{errors.min_data_points}</p>
          )}
          <p className="text-xs text-gray-500 mt-1">Mínimo: 100 puntos</p>
        </div>

        {/* Confidence Threshold */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Umbral de Confianza
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={formData.confidence_threshold}
            onChange={(e) => handleChange('confidence_threshold', parseFloat(e.target.value) || 0)}
            className={`w-full bg-gray-700 border ${
              errors.confidence_threshold ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.confidence_threshold && (
            <p className="text-xs text-red-400 mt-1">{errors.confidence_threshold}</p>
          )}
          <p className="text-xs text-gray-500 mt-1">Rango: 0.0 - 1.0</p>
        </div>

        {/* Spread Threshold */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Umbral de Spread (%)
          </label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="10"
            value={formData.spread_threshold}
            onChange={(e) => handleChange('spread_threshold', parseFloat(e.target.value) || 0)}
            className={`w-full bg-gray-700 border ${
              errors.spread_threshold ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.spread_threshold && (
            <p className="text-xs text-red-400 mt-1">{errors.spread_threshold}</p>
          )}
          <p className="text-xs text-gray-500 mt-1">Rango: 0% - 10%</p>
        </div>
      </div>
    </div>
  )
}

