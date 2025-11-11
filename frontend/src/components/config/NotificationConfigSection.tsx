'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, AlertCircle, CheckCircle, Eye, EyeOff } from 'lucide-react'
import api from '@/lib/api'
import type { NotificationConfig, ConfigUpdateRequest } from '@/types/config'

interface NotificationConfigSectionProps {
  config: NotificationConfig
  onConfigChange: () => void
}

export function NotificationConfigSection({ config, onConfigChange }: NotificationConfigSectionProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<NotificationConfig>(config)
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

  const handleSave = () => {
    setSaveStatus('saving')
    updateMutation.mutate({
      notifications: formData,
    })
  }

  const handleChange = (field: keyof NotificationConfig, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    onConfigChange()
  }

  const maskToken = (token: string | null): string => {
    if (!token) return ''
    if (token.length <= 8) return '••••••••'
    return token.substring(0, 8) + '••••••••'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Configuración de Notificaciones</h2>
          <p className="text-gray-400 text-sm mt-1">
            Configura Telegram y Email para recibir alertas del sistema
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

      <div className="bg-yellow-900/30 border border-yellow-500/50 rounded-lg p-4 mb-6">
        <p className="text-yellow-400 text-sm">
          ⚠️ Los tokens y contraseñas no se pueden actualizar via API por seguridad. 
          Para cambiarlos, modifica el archivo .env y reinicia el servidor.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Enable Notifications */}
        <div>
          <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
            <input
              type="checkbox"
              checked={formData.enable_notifications}
              onChange={(e) => handleChange('enable_notifications', e.target.checked)}
              className="w-4 h-4 rounded bg-gray-700 border-gray-600 text-primary-600 focus:ring-primary-500"
            />
            Habilitar Notificaciones
          </label>
        </div>

        {/* Telegram Bot Token */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Telegram Bot Token
          </label>
          <div className="relative">
            <input
              type="text"
              value={maskToken(formData.telegram_bot_token)}
              disabled
              className="w-full bg-gray-700/50 border border-gray-600 text-gray-400 rounded-lg px-4 py-2 cursor-not-allowed"
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">Solo lectura (configurado en .env)</p>
        </div>

        {/* Telegram Chat ID */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Telegram Chat ID
          </label>
          <input
            type="text"
            value={formData.telegram_chat_id || ''}
            onChange={(e) => handleChange('telegram_chat_id', e.target.value || null)}
            placeholder="Ej: 123456789"
            className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Email SMTP Server */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Servidor SMTP
          </label>
          <input
            type="text"
            value={formData.email_smtp_server || ''}
            onChange={(e) => handleChange('email_smtp_server', e.target.value || null)}
            placeholder="Ej: smtp.gmail.com"
            className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Email SMTP Port */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Puerto SMTP
          </label>
          <input
            type="number"
            min="1"
            max="65535"
            value={formData.email_smtp_port}
            onChange={(e) => handleChange('email_smtp_port', parseInt(e.target.value) || 587)}
            className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Email From */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Email Remitente
          </label>
          <input
            type="email"
            value={formData.email_from || ''}
            onChange={(e) => handleChange('email_from', e.target.value || null)}
            placeholder="Ej: alerts@example.com"
            className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>
    </div>
  )
}

