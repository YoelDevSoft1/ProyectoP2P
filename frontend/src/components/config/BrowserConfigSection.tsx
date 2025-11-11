'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, AlertCircle, CheckCircle } from 'lucide-react'
import api from '@/lib/api'
import type { BrowserConfig, ConfigUpdateRequest } from '@/types/config'

interface BrowserConfigSectionProps {
  config: BrowserConfig
  onConfigChange: () => void
}

export function BrowserConfigSection({ config, onConfigChange }: BrowserConfigSectionProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<BrowserConfig>(config)
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

    if (formData.timeout < 1000 || formData.timeout > 300000) {
      newErrors.timeout = 'El timeout debe estar entre 1000 y 300000 ms'
    }
    if (formData.pool_size < 1 || formData.pool_size > 10) {
      newErrors.pool_size = 'El tamaño del pool debe estar entre 1 y 10'
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
      browser: formData,
    })
  }

  const handleChange = (field: keyof BrowserConfig, value: any) => {
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
          <h2 className="text-2xl font-bold text-white">Configuración de Browser Automation</h2>
          <p className="text-gray-400 text-sm mt-1">
            Configura el navegador automatizado para scraping y automatización
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
        {/* Headless */}
        <div>
          <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
            <input
              type="checkbox"
              checked={formData.headless}
              onChange={(e) => handleChange('headless', e.target.checked)}
              className="w-4 h-4 rounded bg-gray-700 border-gray-600 text-primary-600 focus:ring-primary-500"
            />
            Modo Headless
          </label>
          <p className="text-xs text-gray-500 mt-1">
            Ejecutar el navegador sin interfaz gráfica
          </p>
        </div>

        {/* Timeout */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Timeout (ms)
          </label>
          <input
            type="number"
            min="1000"
            max="300000"
            value={formData.timeout}
            onChange={(e) => handleChange('timeout', parseInt(e.target.value) || 1000)}
            className={`w-full bg-gray-700 border ${
              errors.timeout ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.timeout && (
            <p className="text-xs text-red-400 mt-1">{errors.timeout}</p>
          )}
          <p className="text-xs text-gray-500 mt-1">Rango: 1000 - 300000 ms</p>
        </div>

        {/* Pool Size */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Tamaño del Pool
          </label>
          <input
            type="number"
            min="1"
            max="10"
            value={formData.pool_size}
            onChange={(e) => handleChange('pool_size', parseInt(e.target.value) || 1)}
            className={`w-full bg-gray-700 border ${
              errors.pool_size ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.pool_size && (
            <p className="text-xs text-red-400 mt-1">{errors.pool_size}</p>
          )}
          <p className="text-xs text-gray-500 mt-1">Rango: 1 - 10 navegadores</p>
        </div>
      </div>
    </div>
  )
}

