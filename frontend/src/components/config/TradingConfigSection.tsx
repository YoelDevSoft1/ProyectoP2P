'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, AlertCircle, CheckCircle } from 'lucide-react'
import api from '@/lib/api'
import type { TradingConfig, ConfigUpdateRequest } from '@/types/config'

interface TradingConfigSectionProps {
  config: TradingConfig
  onConfigChange: () => void
}

export function TradingConfigSection({ config, onConfigChange }: TradingConfigSectionProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<TradingConfig>(config)
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

    if (formData.profit_margin_cop < 0 || formData.profit_margin_cop > 10) {
      newErrors.profit_margin_cop = 'El margen debe estar entre 0 y 10%'
    }
    if (formData.profit_margin_ves < 0 || formData.profit_margin_ves > 10) {
      newErrors.profit_margin_ves = 'El margen debe estar entre 0 y 10%'
    }
    if (formData.min_trade_amount < 0) {
      newErrors.min_trade_amount = 'El monto mínimo debe ser mayor o igual a 0'
    }
    if (formData.max_trade_amount < formData.min_trade_amount) {
      newErrors.max_trade_amount = 'El monto máximo debe ser mayor al mínimo'
    }
    if (formData.max_daily_trades < 1 || formData.max_daily_trades > 1000) {
      newErrors.max_daily_trades = 'El número de trades debe estar entre 1 y 1000'
    }
    if (formData.stop_loss_percentage < 0 || formData.stop_loss_percentage > 10) {
      newErrors.stop_loss_percentage = 'El stop loss debe estar entre 0 y 10%'
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
      trading: formData,
    })
  }

  const handleChange = (field: keyof TradingConfig, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    onConfigChange()
    // Limpiar error del campo cuando se modifica
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
          <h2 className="text-2xl font-bold text-white">Configuración de Trading</h2>
          <p className="text-gray-400 text-sm mt-1">
            Configura el modo de trading, márgenes de ganancia y límites de operaciones
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
        {/* Trading Mode */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Modo de Trading
          </label>
          <select
            value={formData.trading_mode}
            onChange={(e) => handleChange('trading_mode', e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="manual">Manual</option>
            <option value="auto">Automático</option>
            <option value="hybrid">Híbrido</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Manual: Requiere aprobación. Auto: Ejecuta automáticamente. Híbrido: Combina ambos.
          </p>
        </div>

        {/* Profit Margin COP */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Margen de Ganancia COP (%)
          </label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="10"
            value={formData.profit_margin_cop}
            onChange={(e) => handleChange('profit_margin_cop', parseFloat(e.target.value) || 0)}
            className={`w-full bg-gray-700 border ${
              errors.profit_margin_cop ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.profit_margin_cop && (
            <p className="text-xs text-red-400 mt-1">{errors.profit_margin_cop}</p>
          )}
        </div>

        {/* Profit Margin VES */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Margen de Ganancia VES (%)
          </label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="10"
            value={formData.profit_margin_ves}
            onChange={(e) => handleChange('profit_margin_ves', parseFloat(e.target.value) || 0)}
            className={`w-full bg-gray-700 border ${
              errors.profit_margin_ves ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.profit_margin_ves && (
            <p className="text-xs text-red-400 mt-1">{errors.profit_margin_ves}</p>
          )}
        </div>

        {/* Min Trade Amount */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Monto Mínimo de Trade (USD)
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={formData.min_trade_amount}
            onChange={(e) => handleChange('min_trade_amount', parseFloat(e.target.value) || 0)}
            className={`w-full bg-gray-700 border ${
              errors.min_trade_amount ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.min_trade_amount && (
            <p className="text-xs text-red-400 mt-1">{errors.min_trade_amount}</p>
          )}
        </div>

        {/* Max Trade Amount */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Monto Máximo de Trade (USD)
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={formData.max_trade_amount}
            onChange={(e) => handleChange('max_trade_amount', parseFloat(e.target.value) || 0)}
            className={`w-full bg-gray-700 border ${
              errors.max_trade_amount ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.max_trade_amount && (
            <p className="text-xs text-red-400 mt-1">{errors.max_trade_amount}</p>
          )}
        </div>

        {/* Max Daily Trades */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Máximo de Trades Diarios
          </label>
          <input
            type="number"
            min="1"
            max="1000"
            value={formData.max_daily_trades}
            onChange={(e) => handleChange('max_daily_trades', parseInt(e.target.value) || 1)}
            className={`w-full bg-gray-700 border ${
              errors.max_daily_trades ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.max_daily_trades && (
            <p className="text-xs text-red-400 mt-1">{errors.max_daily_trades}</p>
          )}
        </div>

        {/* Stop Loss Percentage */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Stop Loss (%)
          </label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="10"
            value={formData.stop_loss_percentage}
            onChange={(e) => handleChange('stop_loss_percentage', parseFloat(e.target.value) || 0)}
            className={`w-full bg-gray-700 border ${
              errors.stop_loss_percentage ? 'border-red-500' : 'border-gray-600'
            } text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500`}
          />
          {errors.stop_loss_percentage && (
            <p className="text-xs text-red-400 mt-1">{errors.stop_loss_percentage}</p>
          )}
          <p className="text-xs text-gray-500 mt-1">
            Porcentaje de pérdida máxima permitida antes de detener operaciones
          </p>
        </div>
      </div>
    </div>
  )
}

