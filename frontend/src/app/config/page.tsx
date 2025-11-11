'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { 
  Home, 
  TrendingUp, 
  Bell, 
  Settings, 
  BarChart3, 
  Activity, 
  Menu, 
  X,
  Save,
  RefreshCw,
  AlertCircle
} from 'lucide-react'
import { getCurrentColombiaTimeString } from '@/lib/dateUtils'
import api from '@/lib/api'
import type { AppConfigResponse } from '@/types/config'
import { TradingConfigSection } from '@/components/config/TradingConfigSection'
import { P2PConfigSection } from '@/components/config/P2PConfigSection'
import { ArbitrageConfigSection } from '@/components/config/ArbitrageConfigSection'
import { NotificationConfigSection } from '@/components/config/NotificationConfigSection'
import { MLConfigSection } from '@/components/config/MLConfigSection'
import { AlphaVantageConfigSection } from '@/components/config/AlphaVantageConfigSection'
import { FXConfigSection } from '@/components/config/FXConfigSection'
import { RateLimitConfigSection } from '@/components/config/RateLimitConfigSection'
import { BrowserConfigSection } from '@/components/config/BrowserConfigSection'

type ConfigSection = 
  | 'trading' 
  | 'p2p' 
  | 'arbitrage' 
  | 'notifications' 
  | 'ml' 
  | 'alpha_vantage' 
  | 'fx' 
  | 'rate_limiting' 
  | 'browser'

export default function ConfigPage() {
  const [currentTime, setCurrentTime] = useState<string>('')
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false)
  const [activeSection, setActiveSection] = useState<ConfigSection>('trading')
  const [hasChanges, setHasChanges] = useState<boolean>(false)

  const { data: config, isLoading, error, refetch } = useQuery<AppConfigResponse>({
    queryKey: ['configuration'],
    queryFn: () => api.getConfiguration(),
    refetchInterval: 30000, // Refrescar cada 30 segundos
  })

  // Update time on client side only
  useEffect(() => {
    const updateTime = () => {
      setCurrentTime(getCurrentColombiaTimeString())
    }
    updateTime()
    const interval = setInterval(updateTime, 1000)
    return () => clearInterval(interval)
  }, [])

  // Prevent body scroll when sidebar is open on mobile
  useEffect(() => {
    if (sidebarOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [sidebarOpen])

  const sections: Array<{ id: ConfigSection; label: string; icon: any }> = [
    { id: 'trading', label: 'Operaciones', icon: BarChart3 },
    { id: 'p2p', label: 'P2P', icon: Activity },
    { id: 'arbitrage', label: 'Arbitraje', icon: TrendingUp },
    { id: 'notifications', label: 'Notificaciones', icon: Bell },
    { id: 'ml', label: 'Aprendizaje Automático', icon: Activity },
    { id: 'alpha_vantage', label: 'Alpha Vantage', icon: Activity },
    { id: 'fx', label: 'FX y Tasas', icon: TrendingUp },
    { id: 'rate_limiting', label: 'Límite de Tasa', icon: Settings },
    { id: 'browser', label: 'Automatización de Navegador', icon: Settings },
  ]

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
          <p className="mt-4 text-gray-400">Cargando configuración...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Error al cargar configuración</h2>
          <p className="text-gray-400 mb-4">
            {error instanceof Error ? error.message : 'Error desconocido'}
          </p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    )
  }

  if (!config) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 w-64 bg-gray-800 border-r border-gray-700 z-50
        transform transition-transform duration-300 ease-in-out
        lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-700">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-primary-500" />
            <span className="ml-2 text-xl font-bold text-white">P2P Dashboard</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-gray-400 hover:text-white"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <nav className="mt-6 px-4 space-y-2">
          <Link
            href="/"
            onClick={() => setSidebarOpen(false)}
            className="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors"
          >
            <Home className="h-5 w-5 mr-3" />
            Página Principal
          </Link>

          <Link
            href="/dashboard"
            onClick={() => setSidebarOpen(false)}
            className="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors"
          >
            <BarChart3 className="h-5 w-5 mr-3" />
            Panel de Control
          </Link>

          <Link
            href="/monitoring"
            onClick={() => setSidebarOpen(false)}
            className="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors"
          >
            <Activity className="h-5 w-5 mr-3" />
            Monitoreo
          </Link>

          <Link
            href="/alerts"
            onClick={() => setSidebarOpen(false)}
            className="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors"
          >
            <Bell className="h-5 w-5 mr-3" />
            Alertas
          </Link>

          <Link
            href="/config"
            onClick={() => setSidebarOpen(false)}
            className="flex items-center px-4 py-3 bg-primary-600 text-white rounded-lg"
          >
            <Settings className="h-5 w-5 mr-3" />
            Configuración
          </Link>
        </nav>
      </div>

      {/* Main Content */}
      <div className="lg:ml-64">
        {/* Header */}
        <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-30">
          <div className="px-4 sm:px-6 lg:px-8 py-3 sm:py-4">
            <div className="flex items-center justify-between gap-3 sm:gap-4">
              <div className="flex items-center gap-2 sm:gap-4 flex-1 min-w-0">
                {/* Mobile Menu Button */}
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="lg:hidden text-gray-400 hover:text-white p-2 -ml-2 flex-shrink-0"
                  aria-label="Abrir menú"
                >
                  <Menu className="h-5 w-5 sm:h-6 sm:w-6" />
                </button>
                <div className="min-w-0 flex-1">
                  <h1 className="text-lg sm:text-xl lg:text-2xl font-bold text-white truncate">
                    Configuración del Sistema
                  </h1>
                  <p className="text-gray-400 text-xs sm:text-sm mt-0.5 hidden sm:block">
                    Gestiona la configuración de trading, P2P, arbitraje y más
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 sm:gap-4">
                <div className="text-right hidden sm:block">
                  <p className="text-xs sm:text-sm text-gray-400">Última actualización</p>
                  <p className="text-white font-medium text-xs sm:text-sm lg:text-base">
                    {currentTime || '--:--:--'}
                  </p>
                </div>
                <button
                  onClick={() => refetch()}
                  className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
                  title="Actualizar"
                >
                  <RefreshCw className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="p-4 sm:p-6 lg:p-8">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Sections Sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 sticky top-24">
                <h2 className="text-lg font-semibold text-white mb-4">Secciones</h2>
                <nav className="space-y-2">
                  {sections.map((section) => {
                    const Icon = section.icon
                    return (
                      <button
                        key={section.id}
                        onClick={() => setActiveSection(section.id)}
                        className={`
                          w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-left
                          ${activeSection === section.id
                            ? 'bg-primary-600 text-white'
                            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                          }
                        `}
                      >
                        <Icon className="h-5 w-5 flex-shrink-0" />
                        <span className="text-sm font-medium">{section.label}</span>
                      </button>
                    )
                  })}
                </nav>
              </div>
            </div>

            {/* Configuration Form */}
            <div className="lg:col-span-3">
              <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 sm:p-6 lg:p-8">
                {activeSection === 'trading' && (
                  <TradingConfigSection 
                    config={config.trading} 
                    onConfigChange={() => setHasChanges(true)}
                  />
                )}
                {activeSection === 'p2p' && (
                  <P2PConfigSection 
                    config={config.p2p} 
                    onConfigChange={() => setHasChanges(true)}
                  />
                )}
                {activeSection === 'arbitrage' && (
                  <ArbitrageConfigSection 
                    config={config.arbitrage} 
                    onConfigChange={() => setHasChanges(true)}
                  />
                )}
                {activeSection === 'notifications' && (
                  <NotificationConfigSection 
                    config={config.notifications} 
                    onConfigChange={() => setHasChanges(true)}
                  />
                )}
                {activeSection === 'ml' && (
                  <MLConfigSection 
                    config={config.ml} 
                    onConfigChange={() => setHasChanges(true)}
                  />
                )}
                {activeSection === 'alpha_vantage' && (
                  <AlphaVantageConfigSection 
                    config={config.alpha_vantage} 
                    onConfigChange={() => setHasChanges(true)}
                  />
                )}
                {activeSection === 'fx' && (
                  <FXConfigSection 
                    config={config.fx} 
                    onConfigChange={() => setHasChanges(true)}
                  />
                )}
                {activeSection === 'rate_limiting' && (
                  <RateLimitConfigSection 
                    config={config.rate_limiting} 
                    onConfigChange={() => setHasChanges(true)}
                  />
                )}
                {activeSection === 'browser' && (
                  <BrowserConfigSection 
                    config={config.browser} 
                    onConfigChange={() => setHasChanges(true)}
                  />
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

