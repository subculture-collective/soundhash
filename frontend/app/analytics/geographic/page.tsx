'use client'

import { GeographicMap } from '@/components/features/analytics/GeographicMap'

export default function GeographicPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Geographic Analytics</h1>
          <p className="text-muted-foreground">
            Analyze user activity and performance by location
          </p>
        </div>

        <GeographicMap />
      </div>
    </div>
  )
}
