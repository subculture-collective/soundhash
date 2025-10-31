'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ChevronDown } from 'lucide-react'

const funnelData = [
  { step: 'Sign Up', users: 10000, percentage: 100, dropOff: 0 },
  { step: 'Email Verification', users: 8500, percentage: 85, dropOff: 15 },
  { step: 'First Upload', users: 6800, percentage: 68, dropOff: 17 },
  { step: 'API Key Generated', users: 5100, percentage: 51, dropOff: 17 },
  { step: 'First Match', users: 4250, percentage: 42.5, dropOff: 8.5 },
]

export function FunnelAnalysis() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>User Journey Funnel</CardTitle>
          <CardDescription>
            Track user progression through key milestones
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {funnelData.map((step, index) => (
              <div key={step.step} className="relative">
                {/* Funnel Step */}
                <div 
                  className="relative overflow-hidden rounded-lg bg-gradient-to-r from-blue-500 to-indigo-600 text-white p-4 transition-all hover:shadow-lg"
                  style={{ 
                    width: `${step.percentage}%`,
                    minWidth: '250px'
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold">{step.step}</div>
                      <div className="text-sm opacity-90">
                        {step.users.toLocaleString()} users ({step.percentage}%)
                      </div>
                    </div>
                    {step.dropOff > 0 && (
                      <div className="text-right">
                        <div className="text-xs opacity-90">Drop-off</div>
                        <div className="font-semibold text-red-200">
                          -{step.dropOff}%
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Arrow between steps */}
                {index < funnelData.length - 1 && (
                  <div className="flex justify-center py-2">
                    <ChevronDown className="h-5 w-5 text-muted-foreground" />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">Overall Conversion</div>
              <div className="text-2xl font-bold text-green-600">42.5%</div>
            </div>
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">Biggest Drop-off</div>
              <div className="text-2xl font-bold text-red-600">17%</div>
              <div className="text-xs text-muted-foreground mt-1">First Upload</div>
            </div>
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">Avg. Time to Convert</div>
              <div className="text-2xl font-bold">3.2 days</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Drop-off Reasons */}
      <Card>
        <CardHeader>
          <CardTitle>Drop-off Analysis</CardTitle>
          <CardDescription>
            Common reasons users leave at each step
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { step: 'Email Verification', reason: 'Email not received', count: 892 },
              { step: 'First Upload', reason: 'File format issues', count: 654 },
              { step: 'First Upload', reason: 'Upload timeout', count: 421 },
              { step: 'API Key Generated', reason: 'Documentation unclear', count: 312 },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between border-b pb-3">
                <div>
                  <div className="font-medium">{item.step}</div>
                  <div className="text-sm text-muted-foreground">{item.reason}</div>
                </div>
                <div className="text-right">
                  <div className="font-semibold">{item.count}</div>
                  <div className="text-xs text-muted-foreground">users</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
