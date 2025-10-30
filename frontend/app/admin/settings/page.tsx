'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">System Configuration</h1>

      <Card>
        <CardHeader>
          <CardTitle>Processing Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Max Concurrent Downloads</label>
            <Input type="number" defaultValue={5} className="mt-1" />
          </div>

          <div>
            <label className="text-sm font-medium">Segment Length (seconds)</label>
            <Input type="number" defaultValue={30} className="mt-1" />
          </div>

          <Button>Save Changes</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>System Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between">
            <span className="text-sm font-medium">Version</span>
            <span className="text-sm text-muted-foreground">1.0.0</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm font-medium">Environment</span>
            <span className="text-sm text-muted-foreground">Production</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
