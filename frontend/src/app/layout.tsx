import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'CambioExpress - Las Mejores Tasas para Cambiar COP y VES | Cambio de Divisas',
  description: 'Cambia COP y VES al mejor precio del mercado. Rápido, seguro y con las mejores tasas garantizadas. Respaldado por Binance P2P. Operaciones en menos de 10 minutos.',
  keywords: [
    'cambio de divisas',
    'mejor tasa COP',
    'mejor tasa VES',
    'cambio COP a USDT',
    'cambio VES a USDT',
    'casa de cambio',
    'binance p2p',
    'cambio rapido',
    'mejor tasa colombia',
    'mejor tasa venezuela',
    'cambio seguro',
    'p2p colombia',
    'p2p venezuela',
    'exchange cop',
    'exchange ves',
  ],
  authors: [{ name: 'CambioExpress' }],
  creator: 'CambioExpress',
  publisher: 'CambioExpress',
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    locale: 'es_CO',
    url: '/',
    siteName: 'CambioExpress',
    title: 'CambioExpress - Las Mejores Tasas para Cambiar COP y VES',
    description: 'Cambia COP y VES al mejor precio del mercado. Rápido, seguro y con las mejores tasas garantizadas. Respaldado por Binance P2P.',
    images: [
      {
        url: '/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'CambioExpress - Mejores Tasas de Cambio',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'CambioExpress - Las Mejores Tasas para Cambiar COP y VES',
    description: 'Cambia COP y VES al mejor precio del mercado. Rápido, seguro y con las mejores tasas garantizadas.',
    images: ['/og-image.jpg'],
    creator: '@CambioExpress',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/site.webmanifest',
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 5,
  },
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#10b981' },
    { media: '(prefers-color-scheme: dark)', color: '#059669' },
  ],
  category: 'finance',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}
