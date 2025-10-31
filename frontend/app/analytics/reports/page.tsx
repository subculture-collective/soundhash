'use client'

import { ReportExporter } from '@/components/features/analytics/ReportExporter'

export default function ReportsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Reports & Exports</h1>
          <p className="text-muted-foreground">
            Generate, schedule, and download custom analytics reports
          </p>
        </div>

        <ReportExporter />
      </div>
    </div>
  )
}
