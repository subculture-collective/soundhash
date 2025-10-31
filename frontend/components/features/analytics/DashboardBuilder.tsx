'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from 'sonner'
import { 
  GripVertical, 
  Plus, 
  Trash2, 
  Settings, 
  BarChart3,
  LineChart as LineChartIcon,
  PieChart,
  Activity,
  TrendingUp
} from 'lucide-react'

interface Widget {
  id: string
  type: string
  title: string
  position: { x: number; y: number }
  size: { w: number; h: number }
}

const widgetTypes = [
  { type: 'line', name: 'Line Chart', icon: LineChartIcon },
  { type: 'bar', name: 'Bar Chart', icon: BarChart3 },
  { type: 'pie', name: 'Pie Chart', icon: PieChart },
  { type: 'metric', name: 'Metric Card', icon: Activity },
  { type: 'trend', name: 'Trend Chart', icon: TrendingUp },
]

export function DashboardBuilder() {
  const [dashboardName, setDashboardName] = useState('My Custom Dashboard')
  const [widgets, setWidgets] = useState<Widget[]>([
    {
      id: '1',
      type: 'line',
      title: 'API Usage',
      position: { x: 0, y: 0 },
      size: { w: 2, h: 1 },
    },
    {
      id: '2',
      type: 'metric',
      title: 'Total Users',
      position: { x: 2, y: 0 },
      size: { w: 1, h: 1 },
    },
  ])
  const [selectedWidget, setSelectedWidget] = useState<string | null>(null)

  const addWidget = (type: string) => {
    const newWidget: Widget = {
      id: Date.now().toString(),
      type,
      title: `New ${type} Widget`,
      position: { x: 0, y: widgets.length },
      size: { w: 2, h: 1 },
    }
    setWidgets([...widgets, newWidget])
  }

  const removeWidget = (id: string) => {
    setWidgets(widgets.filter((w) => w.id !== id))
    if (selectedWidget === id) {
      setSelectedWidget(null)
    }
  }

  const updateWidgetTitle = (id: string, title: string) => {
    setWidgets(widgets.map((w) => (w.id === id ? { ...w, title } : w)))
  }

  const saveDashboard = () => {
    // TODO: Implement API call to save dashboard
    toast.success('Dashboard saved successfully!', {
      description: `"${dashboardName}" has been saved with ${widgets.length} widgets`,
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle>Dashboard Builder</CardTitle>
          <CardDescription>
            Create and customize your analytics dashboard
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">
                Dashboard Name
              </label>
              <Input
                value={dashboardName}
                onChange={(e) => setDashboardName(e.target.value)}
                placeholder="Enter dashboard name"
              />
            </div>
            <Button onClick={saveDashboard} className="gap-2">
              Save Dashboard
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-4">
        {/* Widget Library */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">Widgets</CardTitle>
            <CardDescription className="text-xs">
              Drag widgets to add them
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {widgetTypes.map((widget) => (
              <Button
                key={widget.type}
                variant="outline"
                className="w-full justify-start gap-2"
                onClick={() => addWidget(widget.type)}
              >
                <widget.icon className="h-4 w-4" />
                {widget.name}
              </Button>
            ))}
          </CardContent>
        </Card>

        {/* Canvas */}
        <Card className="md:col-span-3">
          <CardHeader>
            <CardTitle className="text-lg">Dashboard Preview</CardTitle>
            <CardDescription className="text-xs">
              {widgets.length} widgets configured
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="min-h-[600px] border-2 border-dashed rounded-lg p-4 bg-muted/20">
              {widgets.length === 0 ? (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center text-muted-foreground">
                    <Plus className="h-12 w-12 mx-auto mb-2" />
                    <p>No widgets yet</p>
                    <p className="text-sm">Add widgets from the left panel</p>
                  </div>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-3">
                  {widgets.map((widget) => (
                    <Card
                      key={widget.id}
                      className={`cursor-pointer transition-all ${
                        selectedWidget === widget.id
                          ? 'ring-2 ring-blue-500'
                          : ''
                      }`}
                      style={{
                        gridColumn: `span ${widget.size.w}`,
                      }}
                      onClick={() => setSelectedWidget(widget.id)}
                    >
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <GripVertical className="h-4 w-4 text-muted-foreground cursor-move" />
                            <CardTitle className="text-sm">
                              {widget.title}
                            </CardTitle>
                          </div>
                          <div className="flex gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 w-6 p-0"
                              onClick={(e) => {
                                e.stopPropagation()
                                // TODO: Open settings modal
                              }}
                            >
                              <Settings className="h-3 w-3" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 w-6 p-0"
                              onClick={(e) => {
                                e.stopPropagation()
                                removeWidget(widget.id)
                              }}
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="h-32 rounded bg-muted flex items-center justify-center text-sm text-muted-foreground">
                          {widget.type.charAt(0).toUpperCase() +
                            widget.type.slice(1)}{' '}
                          Chart Preview
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Widget Settings Panel (when widget is selected) */}
      {selectedWidget && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Widget Settings</CardTitle>
            <CardDescription>
              Configure the selected widget
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Widget Title
              </label>
              <Input
                value={
                  widgets.find((w) => w.id === selectedWidget)?.title || ''
                }
                onChange={(e) =>
                  updateWidgetTitle(selectedWidget, e.target.value)
                }
                placeholder="Enter widget title"
              />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Data Source
                </label>
                <select className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  <option>API Usage</option>
                  <option>User Activity</option>
                  <option>Revenue</option>
                  <option>Matches</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Time Range
                </label>
                <select className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  <option>Last 7 days</option>
                  <option>Last 30 days</option>
                  <option>Last 90 days</option>
                  <option>Last year</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
