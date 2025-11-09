'use client'

import { useState } from 'react'
import { Download, FileText, Calendar, TrendingUp, DollarSign, BarChart3 } from 'lucide-react'

export function ReportsExport() {
  const [reportType, setReportType] = useState<'daily' | 'weekly' | 'monthly' | 'custom'>('daily')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)

  const handleGenerateReport = async () => {
    setIsGenerating(true)
    // Simular generación de reporte
    await new Promise((resolve) => setTimeout(resolve, 2000))
    setIsGenerating(false)
    // TODO: Llamar a API para generar reporte
  }

  const handleExport = (format: 'csv' | 'pdf' | 'json') => {
    // TODO: Implementar exportación
    console.log(`Exporting as ${format}`)
  }

  const reportTypes = [
    {
      id: 'daily',
      label: 'Reporte Diario',
      description: 'Resumen de operaciones del día',
      icon: Calendar,
    },
    {
      id: 'weekly',
      label: 'Reporte Semanal',
      description: 'Análisis de la última semana',
      icon: BarChart3,
    },
    {
      id: 'monthly',
      label: 'Reporte Mensual',
      description: 'Resumen completo del mes',
      icon: TrendingUp,
    },
    {
      id: 'custom',
      label: 'Reporte Personalizado',
      description: 'Selecciona un rango de fechas',
      icon: FileText,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Reportes y Exportación</h2>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <FileText className="h-4 w-4" />
          <span>Genera reportes detallados de tus operaciones</span>
        </div>
      </div>

      {/* Selección de Tipo de Reporte */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
        <h3 className="text-lg font-bold text-white mb-4">Tipo de Reporte</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {reportTypes.map((type) => {
            const Icon = type.icon
            return (
              <button
                key={type.id}
                onClick={() => setReportType(type.id as any)}
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  reportType === type.id
                    ? 'border-primary-500 bg-primary-500/20'
                    : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <Icon className="h-5 w-5 text-primary-400" />
                  <span className="font-semibold text-white">{type.label}</span>
                </div>
                <p className="text-sm text-gray-400">{type.description}</p>
              </button>
            )
          })}
        </div>

        {/* Rango de Fechas para Reporte Personalizado */}
        {reportType === 'custom' && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Fecha Inicio</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Fecha Fin</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>
        )}

        {/* Botón de Generar */}
        <div className="mt-6">
          <button
            onClick={handleGenerateReport}
            disabled={isGenerating || (reportType === 'custom' && (!startDate || !endDate))}
            className="flex items-center gap-2 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></div>
                Generando...
              </>
            ) : (
              <>
                <FileText className="h-5 w-5" />
                Generar Reporte
              </>
            )}
          </button>
        </div>
      </div>

      {/* Opciones de Exportación */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
        <h3 className="text-lg font-bold text-white mb-4">Exportar Datos</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center justify-center gap-2 px-6 py-4 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-all"
          >
            <Download className="h-5 w-5" />
            <div className="text-left">
              <p className="font-semibold">CSV</p>
              <p className="text-xs text-gray-400">Excel, Sheets</p>
            </div>
          </button>
          <button
            onClick={() => handleExport('pdf')}
            className="flex items-center justify-center gap-2 px-6 py-4 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-all"
          >
            <Download className="h-5 w-5" />
            <div className="text-left">
              <p className="font-semibold">PDF</p>
              <p className="text-xs text-gray-400">Documento</p>
            </div>
          </button>
          <button
            onClick={() => handleExport('json')}
            className="flex items-center justify-center gap-2 px-6 py-4 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-all"
          >
            <Download className="h-5 w-5" />
            <div className="text-left">
              <p className="font-semibold">JSON</p>
              <p className="text-xs text-gray-400">Datos brutos</p>
            </div>
          </button>
        </div>
      </div>

      {/* Información de Reportes */}
      <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/20 border border-blue-700/50 rounded-xl p-6">
        <div className="flex items-start gap-4">
          <DollarSign className="h-6 w-6 text-blue-400 mt-1" />
          <div>
            <h4 className="text-lg font-semibold text-white mb-2">Información de Reportes</h4>
            <ul className="text-sm text-gray-300 space-y-1">
              <li>• Los reportes incluyen todas las operaciones del período seleccionado</li>
              <li>• Se incluyen métricas de rendimiento, ganancias y análisis de riesgo</li>
              <li>• Los datos se exportan en tiempo real desde la base de datos</li>
              <li>• Los reportes PDF incluyen gráficos y visualizaciones</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

