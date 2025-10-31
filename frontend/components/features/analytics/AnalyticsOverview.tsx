'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  Activity, 
  Users, 
  Clock,
  BarChart3,
  AlertCircle
} from 'lucide-react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface AnalyticsOverviewProps {
  loading?: boolean
}

// Mock data for demonstration
const eventData = [
  { date: 'Jan', events: 4000, users: 2400, apiCalls: 2400 },
  { date: 'Feb', events: 3000, users: 1398, apiCalls: 2210 },
  { date: 'Mar', events: 2000, users: 9800, apiCalls: 2290 },
  { date: 'Apr', events: 2780, users: 3908, apiCalls: 2000 },
  { date: 'May', events: 1890, users: 4800, apiCalls: 2181 },
  { date: 'Jun', events: 2390, users: 3800, apiCalls: 2500 },
]

export function AnalyticsOverview({ loading = false }: AnalyticsOverviewProps) {
  if (loading) {
    return (
      <div className="grid gap-6">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="h-24 animate-pulse bg-muted rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="grid gap-6">
      {/* Key Metrics */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Events</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">45,231</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500">+20.1%</span> from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2,350</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500">+12.5%</span> from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">API Calls</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">54,623</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500">+8.2%</span> from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">187ms</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500">-5.3%</span> from last month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Event Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={eventData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="events" 
                  stroke="#8884d8" 
                  strokeWidth={2}
                />
                <Line 
                  type="monotone" 
                  dataKey="users" 
                  stroke="#82ca9d" 
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>API Usage by Month</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={eventData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="apiCalls" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Error Rate */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Error Rate</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              API errors over the last 30 days
            </p>
          </div>
          <AlertCircle className="h-5 w-5 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline gap-2">
            <div className="text-3xl font-bold">2.4%</div>
            <span className="text-sm text-green-500">-0.3% from last month</span>
          </div>
          <div className="mt-4">
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-red-500 w-[2.4%]" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
