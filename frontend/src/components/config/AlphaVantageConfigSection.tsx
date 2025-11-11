'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, AlertCircle, CheckCircle } from 'lucide-react'
import api from '@/lib/api'
import type { AlphaVantageConfig, ConfigUpdateRequest } from '@/types/config'

interface AlphaVantageConfigSectionProps {
  config: AlphaVantageConfig
  onConfigChange: () => void
}

export function AlphaVantageConfigSection({ config, onConfigChange }: AlphaVantageConfigSectionProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<AlphaVantageConfig>(config)
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

    if (formData.cache_ttl < 60 || formData.cache_ttl > 3600) {
      newErrors.cache_ttl = 'El TTL debe estar entre 60 y 3600 segundos'
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
      alpha_vantage: formData,
    })
  }

  const handleChange = (field: keyof AlphaVantageConfig, value: any) => {
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

  const maskApiKey = (key: string | null): string => {
    if (!key) return ''
    if (key.length <= 8) return 'A828MZ96••••••••'
    return key.substring(0, 8) + '••••••••'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Configuración Alpha Vantage</h2>
          <p className="text-gray-400 text-sm mt-1">
            Configura la integración con Alpha Vantage API para datos de mercado
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

      <div className="bg-yellow-900/30 border border-yellow-500/50 rounded-lg p-4 mb-6">
        <p className="text-yellow-400 text-sm">
          ⚠️ La API Key no se puede actualizar via API por seguridad. 
          Para cambiarla, modifica el archivo .env y reinicia el servidor.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* API Key */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            API Key
          </label>
          <input
            type="text"
            value={maskApiKey(formData.api_key)}
            disabled
            className="w-full bg-gray-700/50 border border-gray-600 text-gray-400 rounded-lg px-4 py-2 cursor-not-allowed"
          />
          <p className="text-xs text-gray-500 mt-1">Solo lectura (configurado en .env)</p>
        </div>

        {/* Enabled */}
        <div>
          <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
            <input
              type="checkbox"
              checked={formData.enabled}
              onChange={(e) => handleChange('enabled', e.target.checked)}
              className="w-4 h-4 rounded bg-gray-700 border-gray-600 text-primary-600 focus:ring-primary-500"
            />
            Habilitado
          </label>
        </div>

        {/* Cache TTL */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            TTL de Caché (segundos)
          </label>
          <input
            type="number"
            min="60"
            max="3600"
            value={formData.cache_ttl}
            onChange={(e) => handleChange('cache_ttl', parseInt(e.target.value) || 60)}
            className={`w-full bg-gray-700 border ${
              errors.cache_ttl ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.cache_ttl && (
            <p className="text-xs text-red-400 mt-1">{errors.cache_ttl}</p>
          )}
          <p className="text-xs text-gray-500 mt-1">Rango: 60 - 3600 segundos</p>
        </div>
      </div>
    </div>
  )
}

