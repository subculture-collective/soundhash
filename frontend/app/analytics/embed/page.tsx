'use client'

import { EmbeddableWidget } from '@/components/features/analytics/EmbeddableWidget'

export default function EmbedPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Embeddable Widgets</h1>
          <p className="text-muted-foreground">
            Create white-label analytics widgets for your customers and partners
          </p>
        </div>

        <EmbeddableWidget />
      </div>
    </div>
  )
}
