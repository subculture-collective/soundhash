'use client'

import { useRouter } from 'next/navigation'
import OnboardingWizard from '@/components/onboarding/OnboardingWizard'

export default function OnboardingPage() {
  const router = useRouter()

  const handleComplete = () => {
    // Redirect to dashboard after completion
    router.push('/dashboard')
  }

  const handleDismiss = () => {
    // Allow dismissing and go to dashboard
    router.push('/dashboard')
  }

  return (
    <div className="min-h-screen bg-background">
      <OnboardingWizard onComplete={handleComplete} onDismiss={handleDismiss} />
    </div>
  )
}
