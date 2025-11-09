'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30 * 1000, // 30 segundos - datos considerados frescos
            gcTime: 5 * 60 * 1000, // 5 minutos - tiempo de garbage collection (antes cacheTime)
            refetchOnWindowFocus: false, // No refetch al cambiar de ventana
            refetchOnReconnect: true, // Refetch al reconectar
            retry: (failureCount, error: any) => {
              // Solo reintentar para errores de red o timeout
              if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
                return failureCount < 3 // Máximo 3 reintentos
              }
              // Para errores 5xx, reintentar
              if (error?.response?.status >= 500) {
                return failureCount < 2 // Máximo 2 reintentos
              }
              // Para otros errores, no reintentar
              return false
            },
            retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000), // Exponential backoff
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
