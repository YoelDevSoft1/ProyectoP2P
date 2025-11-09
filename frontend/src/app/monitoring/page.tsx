'use client'

import { SystemHealth } from '@/components/SystemHealth'
import { MetricsDashboard } from '@/components/MetricsDashboard'

export default function MonitoringPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Monitoreo del Sistema</h1>
          <p className="mt-2 text-gray-600">
            Estado de servicios y métricas en tiempo real
          </p>
        </div>

        <div className="space-y-6">
          {/* System Health */}
          <SystemHealth />

          {/* Metrics Dashboard */}
          <MetricsDashboard />
        </div>
      </div>
    </div>
  )
}

