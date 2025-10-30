'use client'

import { useState, useEffect } from 'react'
import { Video, Code, Building2, Check } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { onboardingApi } from '@/lib/api/onboarding'
import type { OnboardingProgress } from '@/lib/types/onboarding'

interface UseCaseStepProps {
  progress: OnboardingProgress | null
  onNext: () => void
}

export default function UseCaseStep({ progress, onNext }: UseCaseStepProps) {
  const [selected, setSelected] = useState<string | null>(progress?.use_case || null)

  const useCases = [
    {
      id: 'content_creator',
      title: 'Content Creator',
      description: 'Protect and track your content across platforms',
      icon: Video,
      features: [
        'Content protection',
        'Usage tracking',
        'Automated takedowns',
        'Revenue optimization',
      ],
    },
    {
      id: 'developer',
      title: 'Developer',
      description: 'Build audio recognition into your applications',
      icon: Code,
      features: [
        'RESTful API access',
        'SDK libraries',
        'Webhooks',
        'Real-time streaming',
      ],
    },
    {
      id: 'enterprise',
      title: 'Enterprise',
      description: 'Large-scale audio fingerprinting solutions',
      icon: Building2,
      features: [
        'Dedicated infrastructure',
        'Custom integrations',
        'Priority support',
        'Advanced analytics',
      ],
    },
  ]

  const handleSelect = async (useCaseId: string) => {
    setSelected(useCaseId)
    
    // Update the use case in backend
    try {
      await onboardingApi.updateProgress({
        use_case: useCaseId as 'content_creator' | 'developer' | 'enterprise',
        use_case_selected: true,
      })
    } catch (error) {
      console.error('Failed to update use case:', error)
    }
  }

  useEffect(() => {
    if (progress?.use_case) {
      setSelected(progress.use_case)
    }
  }, [progress])

  return (
    <div className="flex flex-col h-full">
      <div className="mb-6">
        <h3 className="text-2xl font-bold mb-2">Choose Your Path</h3>
        <p className="text-muted-foreground">
          Select the option that best describes your use case. This helps us personalize your
          experience.
        </p>
      </div>

      <div className="grid gap-4 mb-6">
        {useCases.map((useCase) => (
          <Card
            key={useCase.id}
            className={`cursor-pointer transition-all ${
              selected === useCase.id
                ? 'ring-2 ring-primary bg-primary/5'
                : 'hover:border-primary/50'
            }`}
            onClick={() => handleSelect(useCase.id)}
          >
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-primary/10 rounded-lg">
                  <useCase.icon className="h-6 w-6 text-primary" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="text-lg font-semibold">{useCase.title}</h4>
                    {selected === useCase.id && (
                      <Check className="h-5 w-5 text-primary" />
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground mb-4">
                    {useCase.description}
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    {useCase.features.map((feature) => (
                      <div key={feature} className="flex items-center gap-2 text-sm">
                        <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                        <span>{feature}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {!selected && (
        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground">
            💡 Don&apos;t worry, you can always change this later in your settings
          </p>
        </div>
      )}
    </div>
  )
}
