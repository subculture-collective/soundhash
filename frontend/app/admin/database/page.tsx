'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function DatabasePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Database Management</h1>

      <Card>
        <CardHeader>
          <CardTitle>Database Query Interface</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Database query interface coming soon. Use direct database access for now.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
