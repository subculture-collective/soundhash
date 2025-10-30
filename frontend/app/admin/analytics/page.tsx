'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Download } from 'lucide-react'
import api from '@/lib/api'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

export default function AnalyticsPage() {
  const [dateRange] = useState({
    from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
    to: new Date(),
  })

  const { data, isLoading } = useQuery({
    queryKey: ['admin-analytics', dateRange],
    queryFn: async () => {
      const response = await api.get('/admin/analytics', {
        params: {
          start_date: dateRange.from.toISOString(),
          end_date: dateRange.to.toISOString(),
        },
      })
      return response.data
    },
  })

  const exportData = async () => {
    try {
      const response = await api.get('/admin/analytics', {
        params: {
          start_date: dateRange.from.toISOString(),
          end_date: dateRange.to.toISOString(),
        },
      })

      // Convert to CSV
      const csvData = JSON.stringify(response.data, null, 2)
      const blob = new Blob([csvData], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `analytics-${Date.now()}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Failed to export data:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Analytics & Reports</h1>
        <Button onClick={exportData}>
          <Download className="mr-2 h-4 w-4" />
          Export Data
        </Button>
      </div>

      {isLoading ? (
        <div className="text-center">Loading analytics...</div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* User Growth Chart */}
          <Card>
            <CardHeader>
              <CardTitle>User Growth</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data?.user_growth || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    name="New Users"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Summary Stats */}
          <Card>
            <CardHeader>
              <CardTitle>Summary Statistics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between">
                <span className="text-sm font-medium">Videos Processed</span>
                <span className="text-sm">{data?.videos_processed || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Date Range</span>
                <span className="text-sm">
                  {dateRange.from.toLocaleDateString()} - {dateRange.to.toLocaleDateString()}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
