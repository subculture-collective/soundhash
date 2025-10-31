'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Activity, 
  DollarSign,
  AlertCircle,
  Download
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { AnalyticsOverview } from '@/components/features/analytics/AnalyticsOverview'
import { APIUsageChart } from '@/components/features/analytics/APIUsageChart'
import { FunnelAnalysis } from '@/components/features/analytics/FunnelAnalysis'
import { RevenueChart } from '@/components/features/analytics/RevenueChart'
import { CohortTable } from '@/components/features/analytics/CohortTable'

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate data loading
    const timer = setTimeout(() => setLoading(false), 1000)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">Analytics Dashboard</h1>
            <p className="text-muted-foreground">
              Comprehensive insights into your SoundHash performance
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" className="gap-2">
              <Download className="h-4 w-4" />
              Export Report
            </Button>
          </div>
        </div>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5 lg:w-auto">
            <TabsTrigger value="overview" className="gap-2">
              <BarChart3 className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="api" className="gap-2">
              <Activity className="h-4 w-4" />
              API Usage
            </TabsTrigger>
            <TabsTrigger value="funnel" className="gap-2">
              <TrendingUp className="h-4 w-4" />
              Funnels
            </TabsTrigger>
            <TabsTrigger value="cohorts" className="gap-2">
              <Users className="h-4 w-4" />
              Cohorts
            </TabsTrigger>
            <TabsTrigger value="revenue" className="gap-2">
              <DollarSign className="h-4 w-4" />
              Revenue
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <AnalyticsOverview loading={loading} />
          </TabsContent>

          <TabsContent value="api" className="space-y-6">
            <div className="grid gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>API Usage Trends</CardTitle>
                  <CardDescription>
                    Monitor API calls, response times, and error rates
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <APIUsageChart />
                </CardContent>
              </Card>

              {/* Top Endpoints */}
              <Card>
                <CardHeader>
                  <CardTitle>Top Endpoints</CardTitle>
                  <CardDescription>Most frequently called API endpoints</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {[
                      { endpoint: '/api/v1/matches', calls: 15234, avgTime: 145 },
                      { endpoint: '/api/v1/fingerprints', calls: 12890, avgTime: 234 },
                      { endpoint: '/api/v1/videos', calls: 8976, avgTime: 312 },
                      { endpoint: '/api/v1/channels', calls: 5432, avgTime: 187 },
                    ].map((item) => (
                      <div key={item.endpoint} className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="font-mono text-sm">{item.endpoint}</p>
                          <p className="text-xs text-muted-foreground">
                            {item.calls.toLocaleString()} calls
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium">{item.avgTime}ms</p>
                          <p className="text-xs text-muted-foreground">avg time</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="funnel" className="space-y-6">
            <FunnelAnalysis />
          </TabsContent>

          <TabsContent value="cohorts" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Cohort Analysis</CardTitle>
                <CardDescription>
                  Track user retention and behavior over time
                </CardDescription>
              </CardHeader>
              <CardContent>
                <CohortTable />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="revenue" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-3">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">$45,231</div>
                  <p className="text-xs text-muted-foreground">
                    +20.1% from last month
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">MRR</CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">$12,345</div>
                  <p className="text-xs text-muted-foreground">
                    +12.3% from last month
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Churn Rate</CardTitle>
                  <AlertCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">2.4%</div>
                  <p className="text-xs text-muted-foreground">
                    -0.8% from last month
                  </p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Revenue Trends</CardTitle>
                <CardDescription>
                  Monthly revenue and forecasting
                </CardDescription>
              </CardHeader>
              <CardContent>
                <RevenueChart />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
