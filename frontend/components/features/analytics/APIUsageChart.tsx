'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts'

// Mock data
const data = [
  { time: '00:00', calls: 120, responseTime: 145, errors: 2 },
  { time: '04:00', calls: 89, responseTime: 132, errors: 1 },
  { time: '08:00', calls: 245, responseTime: 178, errors: 5 },
  { time: '12:00', calls: 389, responseTime: 201, errors: 8 },
  { time: '16:00', calls: 312, responseTime: 189, errors: 6 },
  { time: '20:00', calls: 198, responseTime: 156, errors: 3 },
]

export function APIUsageChart() {
  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-sm font-medium mb-4">API Calls Over Time</h3>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorCalls" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Area 
              type="monotone" 
              dataKey="calls" 
              stroke="#8884d8" 
              fillOpacity={1} 
              fill="url(#colorCalls)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div>
        <h3 className="text-sm font-medium mb-4">Response Time & Errors</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="responseTime" 
              stroke="#82ca9d" 
              strokeWidth={2}
              name="Response Time (ms)"
            />
            <Line 
              yAxisId="right"
              type="monotone" 
              dataKey="errors" 
              stroke="#ff6b6b" 
              strokeWidth={2}
              name="Errors"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
