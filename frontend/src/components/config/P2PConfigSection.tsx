'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, AlertCircle, CheckCircle, X } from 'lucide-react'
import api from '@/lib/api'
import type { P2PConfig, ConfigUpdateRequest } from '@/types/config'

interface P2PConfigSectionProps {
  config: P2PConfig
  onConfigChange: () => void
}

export function P2PConfigSection({ config, onConfigChange }: P2PConfigSectionProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<P2PConfig>(config)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle')
  const [saveMessage, setSaveMessage] = useState<string>('')
  const [newAsset, setNewAsset] = useState<string>('')
  const [newFiat, setNewFiat] = useState<string>('')

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

    if (formData.monitored_assets.length === 0) {
      newErrors.monitored_assets = 'Debe haber al menos un asset monitoreado'
    }
    if (formData.monitored_fiats.length === 0) {
      newErrors.monitored_fiats = 'Debe haber al menos un fiat monitoreado'
    }
    if (formData.analysis_rows < 1 || formData.analysis_rows > 100) {
      newErrors.analysis_rows = 'El número de filas debe estar entre 1 y 100'
    }
    if (formData.top_spreads < 1 || formData.top_spreads > 20) {
      newErrors.top_spreads = 'El número de spreads debe estar entre 1 y 20'
    }
    if (formData.price_cache_seconds < 1 || formData.price_cache_seconds > 3600) {
      newErrors.price_cache_seconds = 'El tiempo de caché debe estar entre 1 y 3600 segundos'
    }
    if (formData.min_surplus_usdt < 0) {
      newErrors.min_surplus_usdt = 'El excedente mínimo debe ser mayor o igual a 0'
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
      p2p: formData,
    })
  }

  const handleChange = (field: keyof P2PConfig, value: any) => {
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

  const addAsset = () => {
    if (newAsset.trim() && !formData.monitored_assets.includes(newAsset.trim().toUpperCase())) {
      handleChange('monitored_assets', [...formData.monitored_assets, newAsset.trim().toUpperCase()])
      setNewAsset('')
    }
  }

  const removeAsset = (asset: string) => {
    handleChange('monitored_assets', formData.monitored_assets.filter((a) => a !== asset))
  }

  const addFiat = () => {
    if (newFiat.trim() && !formData.monitored_fiats.includes(newFiat.trim().toUpperCase())) {
      handleChange('monitored_fiats', [...formData.monitored_fiats, newFiat.trim().toUpperCase()])
      setNewFiat('')
    }
  }

  const removeFiat = (fiat: string) => {
    handleChange('monitored_fiats', formData.monitored_fiats.filter((f) => f !== fiat))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Configuración P2P</h2>
          <p className="text-gray-400 text-sm mt-1">
            Configura los assets y fiats monitoreados, análisis y caché de precios
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
        {/* Monitored Assets */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Assets Monitoreados
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={newAsset}
              onChange={(e) => setNewAsset(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addAsset()}
              placeholder="Ej: BTC, ETH"
              className="flex-1 bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <button
              onClick={addAsset}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
            >
              Agregar
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {formData.monitored_assets.map((asset) => (
              <span
                key={asset}
                className="inline-flex items-center gap-2 px-3 py-1 bg-gray-700 text-white rounded-lg"
              >
                {asset}
                <button
                  onClick={() => removeAsset(asset)}
                  className="text-gray-400 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              </span>
            ))}
          </div>
          {errors.monitored_assets && (
            <p className="text-xs text-red-400 mt-1">{errors.monitored_assets}</p>
          )}
        </div>

        {/* Monitored Fiats */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Fiats Monitoreados
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={newFiat}
              onChange={(e) => setNewFiat(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addFiat()}
              placeholder="Ej: COP, VES"
              className="flex-1 bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <button
              onClick={addFiat}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
            >
              Agregar
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {formData.monitored_fiats.map((fiat) => (
              <span
                key={fiat}
                className="inline-flex items-center gap-2 px-3 py-1 bg-gray-700 text-white rounded-lg"
              >
                {fiat}
                <button
                  onClick={() => removeFiat(fiat)}
                  className="text-gray-400 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              </span>
            ))}
          </div>
          {errors.monitored_fiats && (
            <p className="text-xs text-red-400 mt-1">{errors.monitored_fiats}</p>
          )}
        </div>

        {/* Analysis Rows */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Filas de Análisis
          </label>
          <input
            type="number"
            min="1"
            max="100"
            value={formData.analysis_rows}
            onChange={(e) => handleChange('analysis_rows', parseInt(e.target.value) || 1)}
            className={`w-full bg-gray-700 border ${
              errors.analysis_rows ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.analysis_rows && (
            <p className="text-xs text-red-400 mt-1">{errors.analysis_rows}</p>
          )}
        </div>

        {/* Top Spreads */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Top Spreads
          </label>
          <input
            type="number"
            min="1"
            max="20"
            value={formData.top_spreads}
            onChange={(e) => handleChange('top_spreads', parseInt(e.target.value) || 1)}
            className={`w-full bg-gray-700 border ${
              errors.top_spreads ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.top_spreads && (
            <p className="text-xs text-red-400 mt-1">{errors.top_spreads}</p>
          )}
        </div>

        {/* Price Cache Seconds */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Caché de Precios (segundos)
          </label>
          <input
            type="number"
            min="1"
            max="3600"
            value={formData.price_cache_seconds}
            onChange={(e) => handleChange('price_cache_seconds', parseInt(e.target.value) || 1)}
            className={`w-full bg-gray-700 border ${
              errors.price_cache_seconds ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.price_cache_seconds && (
            <p className="text-xs text-red-400 mt-1">{errors.price_cache_seconds}</p>
          )}
        </div>

        {/* Min Surplus USDT */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Excedente Mínimo USDT
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={formData.min_surplus_usdt}
            onChange={(e) => handleChange('min_surplus_usdt', parseFloat(e.target.value) || 0)}
            className={`w-full bg-gray-700 border ${
              errors.min_surplus_usdt ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.min_surplus_usdt && (
            <p className="text-xs text-red-400 mt-1">{errors.min_surplus_usdt}</p>
          )}
        </div>
      </div>
    </div>
  )
}

