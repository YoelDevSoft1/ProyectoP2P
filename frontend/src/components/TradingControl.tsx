'use client'

import { useState } from 'react'
import { Play, Pause, Settings, Zap, Shield, Target, DollarSign, TrendingUp } from 'lucide-react'

type TradingMode = 'manual' | 'auto' | 'hybrid'

interface TradingConfig {
  mode: TradingMode
  enabled: boolean
  maxDailyVolume: number
  maxPositionSize: number
  profitMarginCOP: number
  profitMarginVES: number
  minSpread: number
  riskLimit: number
}

export function TradingControl() {
  const [config, setConfig] = useState<TradingConfig>({
    mode: 'hybrid',
    enabled: true,
    maxDailyVolume: 100000,
    maxPositionSize: 10000,
    profitMarginCOP: 2.5,
    profitMarginVES: 3.0,
    minSpread: 1.0,
    riskLimit: 5000,
  })

  const [isEditing, setIsEditing] = useState(false)

  const handleModeChange = (mode: TradingMode) => {
    setConfig({ ...config, mode })
  }

  const handleToggle = () => {
    setConfig({ ...config, enabled: !config.enabled })
  }

  const handleSave = () => {
    // Aquí se guardaría la configuración en el backend
    setIsEditing(false)
    // TODO: Llamar a API para guardar configuración
  }

  const modeInfo = {
    manual: {
      label: 'Manual',
      description: 'Todas las operaciones requieren aprobación manual',
      icon: Shield,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20',
    },
    auto: {
      label: 'Automático',
      description: 'El sistema ejecuta operaciones automáticamente',
      icon: Zap,
      color: 'text-green-400',
      bgColor: 'bg-green-500/20',
    },
    hybrid: {
      label: 'Híbrido',
      description: 'Operaciones pequeñas automáticas, grandes requieren aprobación',
      icon: Target,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/20',
    },
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Control de Trading</h2>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-all"
          >
            <Settings className="h-4 w-4" />
            {isEditing ? 'Cancelar' : 'Editar'}
          </button>
          {isEditing && (
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-all"
            >
              Guardar Cambios
            </button>
          )}
        </div>
      </div>

      {/* Estado y Control Principal */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-bold text-white mb-1">Estado del Sistema</h3>
            <p className="text-sm text-gray-400">Controla el modo de operación del trading</p>
          </div>
          <button
            onClick={handleToggle}
            className={`relative inline-flex h-12 w-24 items-center rounded-full transition-colors ${
              config.enabled ? 'bg-green-500' : 'bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-10 w-10 transform rounded-full bg-white transition-transform ${
                config.enabled ? 'translate-x-12' : 'translate-x-1'
              }`}
            />
            <span className="absolute left-2 text-white text-xs font-medium">
              {config.enabled ? 'ON' : 'OFF'}
            </span>
          </button>
        </div>

        {/* Modos de Trading */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(modeInfo).map(([mode, info]) => {
            const Icon = info.icon
            const isActive = config.mode === mode
            return (
              <button
                key={mode}
                onClick={() => handleModeChange(mode as TradingMode)}
                disabled={!isEditing}
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  isActive
                    ? 'border-primary-500 bg-primary-500/20'
                    : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
                } ${!isEditing ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`${info.bgColor} p-2 rounded-lg`}>
                    <Icon className={`h-5 w-5 ${info.color}`} />
                  </div>
                  <span className="font-semibold text-white">{info.label}</span>
                  {isActive && (
                    <span className="ml-auto px-2 py-1 bg-primary-600 text-white text-xs rounded-full">
                      Activo
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-400">{info.description}</p>
              </button>
            )
          })}
        </div>
      </div>

      {/* Configuración de Parámetros */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Límites de Volumen */}
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <DollarSign className="h-5 w-5 text-green-400" />
            <h3 className="text-lg font-bold text-white">Límites de Volumen</h3>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Volumen Máximo Diario (USD)</label>
              <input
                type="number"
                value={config.maxDailyVolume}
                onChange={(e) => setConfig({ ...config, maxDailyVolume: parseFloat(e.target.value) || 0 })}
                disabled={!isEditing}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Tamaño Máximo por Posición (USD)</label>
              <input
                type="number"
                value={config.maxPositionSize}
                onChange={(e) => setConfig({ ...config, maxPositionSize: parseFloat(e.target.value) || 0 })}
                disabled={!isEditing}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
              />
            </div>
          </div>
        </div>

        {/* Márgenes de Ganancia */}
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <TrendingUp className="h-5 w-5 text-yellow-400" />
            <h3 className="text-lg font-bold text-white">Márgenes de Ganancia</h3>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Margen COP (%)</label>
              <input
                type="number"
                step="0.1"
                value={config.profitMarginCOP}
                onChange={(e) => setConfig({ ...config, profitMarginCOP: parseFloat(e.target.value) || 0 })}
                disabled={!isEditing}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Margen VES (%)</label>
              <input
                type="number"
                step="0.1"
                value={config.profitMarginVES}
                onChange={(e) => setConfig({ ...config, profitMarginVES: parseFloat(e.target.value) || 0 })}
                disabled={!isEditing}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
              />
            </div>
          </div>
        </div>

        {/* Parámetros de Riesgo */}
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="h-5 w-5 text-red-400" />
            <h3 className="text-lg font-bold text-white">Gestión de Riesgo</h3>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Spread Mínimo (%)</label>
              <input
                type="number"
                step="0.1"
                value={config.minSpread}
                onChange={(e) => setConfig({ ...config, minSpread: parseFloat(e.target.value) || 0 })}
                disabled={!isEditing}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Límite de Riesgo (USD)</label>
              <input
                type="number"
                value={config.riskLimit}
                onChange={(e) => setConfig({ ...config, riskLimit: parseFloat(e.target.value) || 0 })}
                disabled={!isEditing}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
              />
            </div>
          </div>
        </div>

        {/* Estadísticas Rápidas */}
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <Target className="h-5 w-5 text-blue-400" />
            <h3 className="text-lg font-bold text-white">Estadísticas Rápidas</h3>
          </div>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-gray-700/50 rounded-lg">
              <span className="text-sm text-gray-400">Volumen Usado Hoy</span>
              <span className="text-white font-semibold">$0 / ${config.maxDailyVolume.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-700/50 rounded-lg">
              <span className="text-sm text-gray-400">Riesgo Actual</span>
              <span className="text-white font-semibold">$0 / ${config.riskLimit.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-700/50 rounded-lg">
              <span className="text-sm text-gray-400">Estado</span>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                config.enabled
                  ? 'bg-green-500/20 text-green-400 border border-green-500'
                  : 'bg-red-500/20 text-red-400 border border-red-500'
              }`}>
                {config.enabled ? 'Activo' : 'Inactivo'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

