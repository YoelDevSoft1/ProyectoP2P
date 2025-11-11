'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, AlertCircle, CheckCircle, X } from 'lucide-react'
import api from '@/lib/api'
import type { ArbitrageConfig, ConfigUpdateRequest } from '@/types/config'

interface ArbitrageConfigSectionProps {
  config: ArbitrageConfig
  onConfigChange: () => void
}

export function ArbitrageConfigSection({ config, onConfigChange }: ArbitrageConfigSectionProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<ArbitrageConfig>(config)
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
    if (formData.top_opportunities < 1 || formData.top_opportunities > 50) {
      newErrors.top_opportunities = 'El número de oportunidades debe estar entre 1 y 50'
    }
    if (formData.min_liquidity_usdt < 0) {
      newErrors.min_liquidity_usdt = 'La liquidez mínima debe ser mayor o igual a 0'
    }
    if (formData.min_profit < 0) {
      newErrors.min_profit = 'La ganancia mínima debe ser mayor o igual a 0'
    }
    if (formData.update_price_interval < 1 || formData.update_price_interval > 3600) {
      newErrors.update_price_interval = 'El intervalo debe estar entre 1 y 3600 segundos'
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
      arbitrage: formData,
    })
  }

  const handleChange = (field: keyof ArbitrageConfig, value: any) => {
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
          <h2 className="text-2xl font-bold text-white">Configuración de Arbitraje</h2>
          <p className="text-gray-400 text-sm mt-1">
            Configura los parámetros de detección y ejecución de oportunidades de arbitraje
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
              placeholder="Ej: USDT, BTC"
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

        {/* Top Opportunities */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Top Oportunidades
          </label>
          <input
            type="number"
            min="1"
            max="50"
            value={formData.top_opportunities}
            onChange={(e) => handleChange('top_opportunities', parseInt(e.target.value) || 1)}
            className={`w-full bg-gray-700 border ${
              errors.top_opportunities ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.top_opportunities && (
            <p className="text-xs text-red-400 mt-1">{errors.top_opportunities}</p>
          )}
        </div>

        {/* Min Liquidity USDT */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Liquidez Mínima USDT
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={formData.min_liquidity_usdt}
            onChange={(e) => handleChange('min_liquidity_usdt', parseFloat(e.target.value) || 0)}
            className={`w-full bg-gray-700 border ${
              errors.min_liquidity_usdt ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.min_liquidity_usdt && (
            <p className="text-xs text-red-400 mt-1">{errors.min_liquidity_usdt}</p>
          )}
        </div>

        {/* Min Profit */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Ganancia Mínima (%)
          </label>
          <input
            type="number"
            step="0.1"
            min="0"
            value={formData.min_profit}
            onChange={(e) => handleChange('min_profit', parseFloat(e.target.value) || 0)}
            className={`w-full bg-gray-700 border ${
              errors.min_profit ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.min_profit && (
            <p className="text-xs text-red-400 mt-1">{errors.min_profit}</p>
          )}
        </div>

        {/* Update Price Interval */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Intervalo de Actualización (segundos)
          </label>
          <input
            type="number"
            min="1"
            max="3600"
            value={formData.update_price_interval}
            onChange={(e) => handleChange('update_price_interval', parseInt(e.target.value) || 1)}
            className={`w-full bg-gray-700 border ${
              errors.update_price_interval ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.update_price_interval && (
            <p className="text-xs text-red-400 mt-1">{errors.update_price_interval}</p>
          )}
        </div>
      </div>
    </div>
  )
}

