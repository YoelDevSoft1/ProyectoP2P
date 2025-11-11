'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Home, TrendingUp, Bell, Settings, BarChart3, Activity, Menu, X } from 'lucide-react'
import { SystemHealth } from '@/components/SystemHealth'
import { MetricsDashboard } from '@/components/MetricsDashboard'
import { getCurrentColombiaTimeString } from '@/lib/dateUtils'

export default function MonitoringPage() {
  const [currentTime, setCurrentTime] = useState<string>('')
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false)

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
            className="flex items-center px-4 py-3 bg-primary-600 text-white rounded-lg"
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
            className="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors"
          >
            <Settings className="h-5 w-5 mr-3" />
            Configuración
          </Link>
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
                <h1 className="text-lg sm:text-xl lg:text-2xl font-bold text-white truncate">Monitoreo del Sistema</h1>
                <p className="text-gray-400 text-xs sm:text-sm mt-0.5 hidden sm:block">
                  Estado de servicios y métricas en tiempo real
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
          <div className="space-y-4 sm:space-y-6 lg:space-y-8">
            {/* System Health */}
            <SystemHealth />

            {/* Metrics Dashboard */}
            <MetricsDashboard />
          </div>
        </main>
      </div>
    </div>
  )
}

