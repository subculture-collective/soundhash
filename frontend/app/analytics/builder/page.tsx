'use client'

import { DashboardBuilder } from '@/components/features/analytics/DashboardBuilder'

export default function DashboardBuilderPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Dashboard Builder</h1>
          <p className="text-muted-foreground">
            Create and customize your analytics dashboard with drag-and-drop widgets
          </p>
        </div>

        <DashboardBuilder />
      </div>
    </div>
  )
}
