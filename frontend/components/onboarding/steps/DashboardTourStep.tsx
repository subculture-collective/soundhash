'use client'

import { BarChart3, FileAudio, Search, Settings, CheckCircle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import type { OnboardingProgress } from '@/lib/types/onboarding'

interface DashboardTourStepProps {
  progress: OnboardingProgress | null
  onNext: () => void
}

export default function DashboardTourStep({}: DashboardTourStepProps) {
  const features = [
    {
      icon: FileAudio,
      title: 'Audio Library',
      description: 'Manage all your uploaded audio files and fingerprints in one place',
      color: 'blue',
    },
    {
      icon: Search,
      title: 'Match Results',
      description: 'View detailed match reports with confidence scores and timestamps',
      color: 'green',
    },
    {
      icon: BarChart3,
      title: 'Analytics',
      description: 'Track usage patterns, success rates, and performance metrics',
      color: 'purple',
    },
    {
      icon: Settings,
      title: 'Settings',
      description: 'Customize your account, API keys, and notification preferences',
      color: 'orange',
    },
  ]

  return (
    <div className="flex flex-col h-full">
      <div className="mb-6">
        <h3 className="text-2xl font-bold mb-2">Explore Your Dashboard</h3>
        <p className="text-muted-foreground">
          Here&apos;s a quick overview of the key features available to you
        </p>
      </div>

      <div className="grid gap-4 mb-6">
        {features.map((feature) => (
          <Card key={feature.title} className="hover:border-primary/50 transition-colors">
            <CardContent className="p-5">
              <div className="flex items-start gap-4">
                <div className={`p-2.5 bg-${feature.color}-500/10 rounded-lg`}>
                  <feature.icon className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold mb-1">{feature.title}</h4>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </div>
                <CheckCircle className="h-5 w-5 text-muted-foreground/30" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-auto space-y-4">
        <Card className="border-primary/50 bg-primary/5">
          <CardContent className="p-4">
            <h4 className="font-semibold mb-2 text-sm">💡 Pro Tip</h4>
            <p className="text-sm text-muted-foreground">
              Use the search bar at the top to quickly navigate between features. You can also use
              keyboard shortcuts – press <kbd className="px-2 py-1 bg-muted rounded text-xs">?</kbd>{' '}
              to see all shortcuts.
            </p>
          </CardContent>
        </Card>

        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground">
            Ready to explore? Click &quot;Next&quot; to continue with optional platform integration setup.
          </p>
        </div>
      </div>
    </div>
  )
}
