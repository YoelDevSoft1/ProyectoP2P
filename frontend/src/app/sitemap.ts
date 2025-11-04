import type { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
  const base = (process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000').replace(/\/$/, '')
  const now = new Date().toISOString()

  return [
    {
      url: `${base}/`,
      lastModified: now,
      changeFrequency: 'always',
      priority: 1,
    },
    {
      url: `${base}/dashboard`,
      lastModified: now,
      changeFrequency: 'hourly',
      priority: 0.6,
    },
  ]
}

