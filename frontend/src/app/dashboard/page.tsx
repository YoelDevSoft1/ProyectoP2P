'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { Home, TrendingUp, Bell, Settings, BarChart3, Activity, Shield, Zap, Target, DollarSign, Wallet, LineChart, FileText, Menu, X, Brain } from 'lucide-react'
import api from '@/lib/api'
import { getCurrentColombiaTimeString } from '@/lib/dateUtils'
import { DashboardStats } from '@/components/DashboardStats'
import { RecentTrades } from '@/components/RecentTrades'
import { AlertsList } from '@/components/AlertsList'
import { OrderbookDepth } from '@/components/OrderbookDepth'
import { RiskMetricsDashboard } from '@/components/RiskMetricsDashboard'
import { TriangleArbitrageOpportunities } from '@/components/TriangleArbitrageOpportunities'
import { CompetitivePricingDashboard } from '@/components/CompetitivePricingDashboard'
import { AdvancedMetrics } from '@/components/AdvancedMetrics'
import { PerformanceCharts } from '@/components/PerformanceCharts'
import { InventoryManager } from '@/components/InventoryManager'
import { TradingControl } from '@/components/TradingControl'
import { P2PTradingPanel } from '@/components/P2PTradingPanel'
import { MarketAnalysis } from '@/components/MarketAnalysis'
import { ReportsExport } from '@/components/ReportsExport'
import { ForexExpertTrading } from '@/components/ForexExpertTrading'
import { MLInsights } from '@/components/MLInsights'

type TabType = 'overview' | 'metrics' | 'performance' | 'inventory' | 'trading' | 'ml' | 'market' | 'reports' | 'arbitrage' | 'liquidity' | 'risk' | 'pricing'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [currentTime, setCurrentTime] = useState<string>('')
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false)

  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => api.getDashboardData(),
    refetchInterval: 15000, // Cada 15 segundos
  })

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'metrics', label: 'Métricas', icon: Target },
    { id: 'performance', label: 'Rendimiento', icon: LineChart },
    { id: 'inventory', label: 'Inventario', icon: Wallet },
    { id: 'trading', label: 'Trading', icon: Zap },
    { id: 'ml', label: 'ML Insights', icon: Brain },
    { id: 'market', label: 'Mercado', icon: Activity },
    { id: 'reports', label: 'Reportes', icon: FileText },
    { id: 'arbitrage', label: 'Arbitraje', icon: Zap },
    { id: 'pricing', label: 'Pricing', icon: DollarSign },
    { id: 'liquidity', label: 'Liquidez', icon: Activity },
    { id: 'risk', label: 'Riesgo', icon: Shield },
  ]

  // Update time on client side only to avoid hydration mismatch
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
            Landing Page
          </Link>

          <Link
            href="/dashboard"
            onClick={() => setSidebarOpen(false)}
            className="flex items-center px-4 py-3 bg-primary-600 text-white rounded-lg"
          >
            <BarChart3 className="h-5 w-5 mr-3" />
            Dashboard
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
            {dashboardData?.alerts?.unread > 0 && (
              <span className="ml-auto bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                {dashboardData.alerts.unread}
              </span>
            )}
          </Link>

          <button
            className="flex items-center w-full px-4 py-3 text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors"
            disabled
          >
            <Settings className="h-5 w-5 mr-3" />
            Configuración
          </button>
        </nav>
      </div>

      {/* Main Content */}
      <div className="lg:ml-64">
        {/* Header */}
        <header className="bg-gray-800 border-b border-gray-700 px-4 sm:px-6 lg:px-8 py-3 sm:py-4">
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
                <h1 className="text-lg sm:text-xl lg:text-2xl font-bold text-white truncate">Dashboard</h1>
                <p className="text-gray-400 text-xs sm:text-sm mt-0.5 hidden sm:block">
                  Monitoreo y análisis de operaciones P2P
                </p>
              </div>
            </div>
            <div className="text-right flex-shrink-0 hidden sm:block">
              <p className="text-xs sm:text-sm text-gray-400">Última actualización</p>
              <p className="text-white font-medium text-xs sm:text-sm lg:text-base">
                {currentTime || '--:--:--'}
              </p>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="p-4 sm:p-6 lg:p-8">
          {/* Tabs Navigation */}
          <div className="mb-6 lg:mb-8">
            {/* Mobile: Scrollable tabs with smaller size */}
            <div className="relative">
              <div className="flex gap-2 overflow-x-auto pb-2 scroll-smooth tabs-scroll-container">
                {tabs.map((tab) => {
                  const Icon = tab.icon
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as TabType)}
                      className={`
                        flex items-center gap-1 sm:gap-2 
                        px-3 py-2 sm:px-4 sm:py-2.5 lg:px-6 lg:py-3 
                        rounded-lg font-medium transition-all whitespace-nowrap
                        flex-shrink-0
                        ${activeTab === tab.id
                          ? 'bg-primary-600 text-white shadow-lg shadow-primary-600/50'
                          : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
                        }
                      `}
                    >
                      <Icon className="h-4 w-4 sm:h-5 sm:w-5 flex-shrink-0" />
                      <span className="text-xs sm:text-sm lg:text-base">{tab.label}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          {isLoading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
              <p className="mt-4 text-gray-400">Cargando datos...</p>
            </div>
          ) : (
            <>
              {/* Overview Tab */}
              {activeTab === 'overview' && (
                <div className="space-y-4 sm:space-y-6 lg:space-y-8">
                  {/* Stats Grid */}
                  <DashboardStats data={dashboardData} />

                  {/* Two Column Layout */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8">
                    {/* Recent Trades */}
                    <RecentTrades />

                    {/* Alerts */}
                    <AlertsList />
                  </div>

                  {/* Quick Market Overview */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8">
                    <OrderbookDepth asset="USDT" fiat="COP" />
                    <OrderbookDepth asset="USDT" fiat="VES" />
                  </div>
                </div>
              )}

              {/* Advanced Metrics Tab */}
              {activeTab === 'metrics' && (
                <div className="space-y-4 sm:space-y-6 lg:space-y-8">
                  <AdvancedMetrics />
                </div>
              )}

              {/* Performance Tab */}
              {activeTab === 'performance' && (
                <div className="space-y-4 sm:space-y-6 lg:space-y-8">
                  <PerformanceCharts />
                </div>
              )}

              {/* Inventory Tab */}
              {activeTab === 'inventory' && (
                <div className="space-y-4 sm:space-y-6 lg:space-y-8">
                  <InventoryManager />
                </div>
              )}

              {/* Trading Control Tab */}
              {activeTab === 'trading' && (
                <div className="space-y-4 sm:space-y-6 lg:space-y-8">
                  <ForexExpertTrading />
                  <TradingControl />
                  <P2PTradingPanel />
                </div>
              )}

              {/* Machine Learning Tab */}
              {activeTab === 'ml' && (
                <div className="space-y-4 sm:space-y-6 lg:space-y-8">
                  <MLInsights />
                </div>
              )}

              {/* Market Analysis Tab */}
              {activeTab === 'market' && (
                <div className="space-y-4 sm:space-y-6 lg:space-y-8">
                  <MarketAnalysis />
                </div>
              )}

              {/* Reports Tab */}
              {activeTab === 'reports' && (
                <div className="space-y-4 sm:space-y-6 lg:space-y-8">
                  <ReportsExport />
                </div>
              )}

              {/* Triangle Arbitrage Tab */}
              {activeTab === 'arbitrage' && (
                <div className="space-y-4 sm:space-y-6 lg:space-y-8">
                  <TriangleArbitrageOpportunities />
                </div>
              )}

              {/* Competitive Pricing Tab */}
              {activeTab === 'pricing' && (
                <div className="space-y-4 sm:space-y-6 lg:space-y-8">
                  <CompetitivePricingDashboard />
                </div>
              )}

              {/* Liquidity Analysis Tab */}
              {activeTab === 'liquidity' && (
                <div className="space-y-4 sm:space-y-6 lg:space-y-8">
                  <div className="grid grid-cols-1 gap-4 sm:gap-6 lg:gap-8">
                    <div>
                      <h3 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">COP Market</h3>
                      <OrderbookDepth asset="USDT" fiat="COP" />
                    </div>

                    <div>
                      <h3 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">VES Market</h3>
                      <OrderbookDepth asset="USDT" fiat="VES" />
                    </div>
                  </div>
                </div>
              )}

              {/* Risk Management Tab */}
              {activeTab === 'risk' && (
                <div className="space-y-4 sm:space-y-6 lg:space-y-8">
                  <RiskMetricsDashboard />

                  {/* Info Message */}
                  <div className="bg-blue-900/30 border border-blue-500/50 rounded-xl p-4 sm:p-6">
                    <div className="flex items-start gap-3 sm:gap-4">
                      <Shield className="h-5 w-5 sm:h-6 sm:w-6 text-blue-400 mt-1 flex-shrink-0" />
                      <div>
                        <h4 className="text-base sm:text-lg font-semibold text-white mb-2">
                          Gestión de Riesgo Profesional
                        </h4>
                        <p className="text-gray-300 text-xs sm:text-sm mb-3">
                          Las métricas de riesgo se generarán automáticamente una vez que el sistema acumule suficientes datos de trading.
                        </p>
                        <ul className="text-xs sm:text-sm text-gray-400 space-y-1">
                          <li>• Mínimo 30 operaciones para calcular métricas básicas</li>
                          <li>• Mínimo 100 operaciones para análisis estadístico robusto</li>
                          <li>• Los datos se actualizan en tiempo real conforme operas</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  )
}
