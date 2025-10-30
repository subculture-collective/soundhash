'use client'

import { useQuery } from '@tanstack/react-query'
import { 
  Users, 
  Database, 
  Activity, 
  AlertTriangle,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { MetricCard } from '@/components/admin/MetricCard'
import api from '@/lib/api'
import { cn } from '@/lib/utils'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

export default function AdminDashboard() {
  const { data: stats } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: async () => {
      const response = await api.get('/admin/stats')
      return response.data
    },
    refetchInterval: 30000, // Refresh every 30s
  })

  const { data: healthCheck } = useQuery({
    queryKey: ['health-check'],
    queryFn: async () => {
      const response = await api.get('/admin/health')
      return response.data
    },
    refetchInterval: 10000, // Refresh every 10s
  })

  // Mock data for charts - in production this would come from API
  const apiUsageData = [
    { date: 'Mon', requests: 1200 },
    { date: 'Tue', requests: 1500 },
    { date: 'Wed', requests: 1800 },
    { date: 'Thu', requests: 1400 },
    { date: 'Fri', requests: 2100 },
    { date: 'Sat', requests: 1600 },
    { date: 'Sun', requests: 1300 },
  ]

  const jobStatusData = stats?.jobs ? [
    { status: 'Pending', count: stats.jobs.pending },
    { status: 'Running', count: stats.jobs.running },
    { status: 'Failed', count: stats.jobs.failed },
  ] : []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">System Overview</h1>
        <div className="flex items-center gap-2">
          <div
            className={cn(
              'h-3 w-3 rounded-full',
              healthCheck?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
            )}
          />
          <span className="text-sm font-medium">
            {healthCheck?.status === 'healthy' ? 'System Healthy' : 'Issues Detected'}
          </span>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          icon={<Users className="h-6 w-6" />}
          title="Total Users"
          value={stats?.users?.total || 0}
        />
        <MetricCard
          icon={<Database className="h-6 w-6" />}
          title="Total Videos"
          value={stats?.videos?.total?.toLocaleString() || 0}
        />
        <MetricCard
          icon={<Activity className="h-6 w-6" />}
          title="Active Jobs"
          value={((stats?.jobs?.pending || 0) + (stats?.jobs?.running || 0))}
        />
        <MetricCard
          icon={<AlertTriangle className="h-6 w-6" />}
          title="Failed Jobs"
          value={stats?.jobs?.failed || 0}
          variant="danger"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* API Usage Chart */}
        <Card>
          <CardHeader>
            <CardTitle>API Usage (Last 7 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={apiUsageData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="requests"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Requests"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Processing Jobs Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Processing Jobs Status</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={jobStatusData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="status" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#3b82f6" name="Jobs" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* System Info */}
      <Card>
        <CardHeader>
          <CardTitle>System Status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Database</span>
            <span className={cn(
              "text-sm",
              healthCheck?.database === 'healthy' ? 'text-green-600' : 'text-red-600'
            )}>
              {healthCheck?.database || 'Unknown'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Active Users</span>
            <span className="text-sm">{stats?.users?.active || 0}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Processed Videos</span>
            <span className="text-sm">{stats?.videos?.processed || 0}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Pending Videos</span>
            <span className="text-sm">{stats?.videos?.pending || 0}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
