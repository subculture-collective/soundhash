'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart, ComposedChart, Bar } from 'recharts'

const revenueData = [
  { month: 'Jan', revenue: 12500, mrr: 11200, forecast: null },
  { month: 'Feb', revenue: 14200, mrr: 12800, forecast: null },
  { month: 'Mar', revenue: 16800, mrr: 14500, forecast: null },
  { month: 'Apr', revenue: 19200, mrr: 16200, forecast: null },
  { month: 'May', revenue: 22100, mrr: 18900, forecast: null },
  { month: 'Jun', revenue: 24500, mrr: 21000, forecast: null },
  { month: 'Jul', revenue: null, mrr: null, forecast: 27500 },
  { month: 'Aug', revenue: null, mrr: null, forecast: 30200 },
  { month: 'Sep', revenue: null, mrr: null, forecast: 33100 },
]

const customersData = [
  { month: 'Jan', new: 45, churned: 8, active: 520 },
  { month: 'Feb', new: 52, churned: 6, active: 566 },
  { month: 'Mar', new: 61, churned: 9, active: 618 },
  { month: 'Apr', new: 58, churned: 7, active: 669 },
  { month: 'May', new: 72, churned: 5, active: 736 },
  { month: 'Jun', new: 68, churned: 8, active: 796 },
]

export function RevenueChart() {
  return (
    <div className="space-y-8">
      {/* Revenue and Forecast */}
      <div>
        <h3 className="text-sm font-medium mb-4">Revenue Trends & Forecast</h3>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={revenueData}>
            <defs>
              <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip 
              formatter={(value: number) => `$${value?.toLocaleString()}`}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#8884d8"
              fillOpacity={1}
              fill="url(#colorRevenue)"
              name="Actual Revenue"
            />
            <Line
              type="monotone"
              dataKey="mrr"
              stroke="#82ca9d"
              strokeWidth={2}
              name="MRR"
            />
            <Line
              type="monotone"
              dataKey="forecast"
              stroke="#ffc658"
              strokeWidth={2}
              strokeDasharray="5 5"
              name="Forecast"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Customer Growth */}
      <div>
        <h3 className="text-sm font-medium mb-4">Customer Growth</h3>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={customersData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar 
              yAxisId="left"
              dataKey="new" 
              fill="#82ca9d" 
              name="New Customers"
            />
            <Bar 
              yAxisId="left"
              dataKey="churned" 
              fill="#ff6b6b" 
              name="Churned"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="active"
              stroke="#8884d8"
              strokeWidth={2}
              name="Active Customers"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">ARPU</div>
          <div className="text-2xl font-bold">$30.78</div>
          <div className="text-xs text-green-500 mt-1">+8.3% from last month</div>
        </div>
        <div className="rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">Customer LTV</div>
          <div className="text-2xl font-bold">$892</div>
          <div className="text-xs text-green-500 mt-1">+12.1% from last month</div>
        </div>
        <div className="rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">Growth Rate</div>
          <div className="text-2xl font-bold">18.2%</div>
          <div className="text-xs text-muted-foreground mt-1">Month over month</div>
        </div>
      </div>
    </div>
  )
}
