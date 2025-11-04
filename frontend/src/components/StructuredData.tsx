type PriceData = {
  fiat: string
  sell_price: number
  buy_price: number
  margin: number
  spread: number
  timestamp: string
}

type PriceResponse = Record<string, PriceData>

type TradeStats = {
  completed: number
  total_profit: number
  total_volume_usd: number
  period_days: number
  success_rate: number
}

type TrmResponse = {
  current: number
  change_percentage: number
  last_updated: string
}

interface StructuredDataProps {
  prices?: PriceResponse | null
  stats?: TradeStats | null
  trm?: TrmResponse | null
}

const baseUrl = (process.env.NEXT_PUBLIC_BASE_URL || '').replace(/\/$/, '') || 'https://cambioexpress.com'
const whatsappNumber = (process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || '').replace(/\D/g, '')

export function StructuredData({ prices, stats, trm }: StructuredDataProps) {
  const offers = Object.entries(prices ?? {}).map(([currency, data]) => ({
    '@type': 'Offer',
    name: `Cambio ${currency}`,
    priceCurrency: currency,
    availability: 'https://schema.org/InStock',
    url: `${baseUrl}/#tasas`,
    priceSpecification: {
      '@type': 'UnitPriceSpecification',
      price: Number(data.sell_price.toFixed(2)),
      priceCurrency: currency,
      referenceQuantity: {
        '@type': 'QuantitativeValue',
        value: 1,
        unitCode: 'E27', // unidad monetaria
      },
      minPrice: Number(data.buy_price.toFixed(2)),
      maxPrice: Number(data.sell_price.toFixed(2)),
    },
    offeredBy: {
      '@type': 'FinancialService',
      name: 'CambioExpress',
    },
    validFrom: new Date(data.timestamp).toISOString(),
  }))

  const catalogItems = Object.entries(prices ?? {}).map(([currency, data]) => ({
    '@type': 'Offer',
    itemOffered: {
      '@type': 'Service',
      name: `Cambio ${currency}`,
      description: `Servicio de cambio para ${currency} con margen actual ${data.margin.toFixed(2)}%`,
    },
  }))

  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'FinancialService',
    name: 'CambioExpress',
    description:
      'Casa de cambio especializada en operaciones Binance P2P para COP y VES. Tasas en tiempo real y ejecución garantizada.',
    url: baseUrl,
    logo: `${baseUrl}/logo.png`,
    image: `${baseUrl}/og-image.jpg`,
    telephone: whatsappNumber ? `+${whatsappNumber}` : undefined,
    priceRange: '$$',
    currenciesAccepted: ['COP', 'VES', 'USDT'],
    paymentAccepted: ['P2P Transfer', 'Bank Transfer', 'Cryptocurrency'],
    areaServed: [
      {
        '@type': 'Country',
        name: 'Colombia',
      },
      {
        '@type': 'Country',
        name: 'Venezuela',
      },
    ],
    availableLanguage: ['Spanish'],
    openingHoursSpecification: {
      '@type': 'OpeningHoursSpecification',
      dayOfWeek: [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday',
      ],
      opens: '00:00',
      closes: '23:59',
    },
    makesOffer: offers,
    serviceOutput: stats
      ? {
          '@type': 'QuantitativeValue',
          value: Number(stats.total_volume_usd.toFixed(2)),
          unitText: 'USDT negociados en los últimos días',
          additionalProperty: [
            {
              '@type': 'PropertyValue',
              name: 'Operaciones completadas',
              value: stats.completed,
            },
            {
              '@type': 'PropertyValue',
              name: 'Rentabilidad neta',
              value: Number(stats.total_profit.toFixed(2)),
              unitCode: 'USD',
            },
            {
              '@type': 'PropertyValue',
              name: 'Periodo analizado',
              value: `${stats.period_days} días`,
            },
          ],
        }
      : undefined,
    contactPoint: whatsappNumber
      ? [
          {
            '@type': 'ContactPoint',
            contactType: 'customer support',
            telephone: `+${whatsappNumber}`,
            areaServed: ['CO', 'VE'],
            availableLanguage: ['es'],
          },
        ]
      : undefined,
    potentialAction: whatsappNumber
      ? {
          '@type': 'CommunicateAction',
          target: `https://wa.me/${whatsappNumber}`,
          description: 'Contacta por WhatsApp para cerrar tu operación de cambio',
        }
      : undefined,
    knowsAbout: ['Cambio COP a USDT', 'Cambio VES a USDT', 'Arbitraje COP/VES'],
    hasOfferCatalog:
      catalogItems.length > 0
        ? {
            '@type': 'OfferCatalog',
            name: 'Servicios ExpressExchange',
            itemListElement: catalogItems,
          }
        : undefined,
  }

  const breadcrumbData = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Inicio',
        item: baseUrl,
      },
    ],
  }

  const trmData =
    trm && trm.current
      ? {
          '@context': 'https://schema.org',
          '@type': 'Dataset',
          name: 'TRM Colombia tiempo real',
          description: 'Tasa representativa del mercado (TRM) de Colombia integrada al motor de ExpressExchange.',
          creator: {
            '@type': 'Organization',
            name: 'CambioExpress',
          },
          variableMeasured: {
            '@type': 'PropertyValue',
            name: 'TRM',
            value: Number(trm.current.toFixed(2)),
            unitCode: 'COP',
            observationDate: trm.last_updated,
          },
        }
      : null

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbData) }}
      />
      {trmData && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(trmData) }}
        />
      )}
    </>
  )
}
