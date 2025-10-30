'use client'

import { Sparkles, Zap, Shield, TrendingUp } from 'lucide-react'
import type { OnboardingProgress } from '@/lib/types/onboarding'

interface WelcomeStepProps {
  progress: OnboardingProgress | null
  onNext: () => void
}

export default function WelcomeStep({ progress, onNext }: WelcomeStepProps) {
  const features = [
    {
      icon: Zap,
      title: 'Lightning Fast',
      description: 'Match audio clips in seconds with our advanced fingerprinting technology',
    },
    {
      icon: Shield,
      title: 'Secure & Private',
      description: 'Your data is encrypted and protected with enterprise-grade security',
    },
    {
      icon: TrendingUp,
      title: 'Scalable',
      description: 'From a few clips to millions, our system grows with your needs',
    },
  ]

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-primary/10 rounded-lg">
          <Sparkles className="h-8 w-8 text-primary" />
        </div>
        <div>
          <h3 className="text-2xl font-bold">Welcome to SoundHash!</h3>
          <p className="text-muted-foreground">
            The most powerful audio fingerprinting platform
          </p>
        </div>
      </div>

      <div className="prose prose-sm dark:prose-invert mb-6">
        <p>
          SoundHash helps you identify and match audio content across YouTube and other platforms
          using advanced audio fingerprinting technology. Whether you&apos;re protecting content,
          tracking usage, or building innovative applications, we&apos;ve got you covered.
        </p>
      </div>

      <div className="grid gap-4 mb-6">
        {features.map((feature) => (
          <div
            key={feature.title}
            className="flex items-start gap-4 p-4 rounded-lg border bg-card"
          >
            <div className="p-2 bg-primary/10 rounded-lg">
              <feature.icon className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold mb-1">{feature.title}</h4>
              <p className="text-sm text-muted-foreground">{feature.description}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-auto">
        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground">
            <strong>Estimated time:</strong> 5-10 minutes to complete
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            You can always come back and finish later
          </p>
        </div>
      </div>
    </div>
  )
}
