'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, Circle, ArrowRight, ArrowLeft, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { onboardingApi } from '@/lib/api/onboarding'
import type { OnboardingProgress } from '@/lib/types/onboarding'

import WelcomeStep from './steps/WelcomeStep'
import UseCaseStep from './steps/UseCaseStep'
import ApiKeyStep from './steps/ApiKeyStep'
import FirstUploadStep from './steps/FirstUploadStep'
import DashboardTourStep from './steps/DashboardTourStep'
import IntegrationStep from './steps/IntegrationStep'

interface OnboardingWizardProps {
  onComplete?: () => void
  onDismiss?: () => void
}

export default function OnboardingWizard({ onComplete, onDismiss }: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState<OnboardingProgress | null>(null)
  const [loading, setLoading] = useState(true)

  const steps = [
    {
      id: 0,
      title: 'Welcome',
      description: 'Get started with SoundHash',
      component: WelcomeStep,
      field: 'welcome_completed' as const,
    },
    {
      id: 1,
      title: 'Choose Your Path',
      description: 'Select your use case',
      component: UseCaseStep,
      field: 'use_case_selected' as const,
    },
    {
      id: 2,
      title: 'API Key',
      description: 'Generate your API key',
      component: ApiKeyStep,
      field: 'api_key_generated' as const,
    },
    {
      id: 3,
      title: 'First Upload',
      description: 'Try uploading audio',
      component: FirstUploadStep,
      field: 'first_upload_completed' as const,
    },
    {
      id: 4,
      title: 'Explore Dashboard',
      description: 'Discover key features',
      component: DashboardTourStep,
      field: 'dashboard_explored' as const,
    },
    {
      id: 5,
      title: 'Integration',
      description: 'Connect your platform (optional)',
      component: IntegrationStep,
      field: 'integration_started' as const,
    },
  ]

  useEffect(() => {
    loadProgress()
  }, [])

  const loadProgress = async () => {
    try {
      const data = await onboardingApi.getProgress()
      setProgress(data)
      setCurrentStep(data.current_step || 0)
    } catch (error) {
      console.error('Failed to load onboarding progress:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateStep = async (stepIndex: number, completed: boolean = true) => {
    if (!progress) return

    const step = steps[stepIndex]
    const updates: Partial<OnboardingProgress> = {
      current_step: stepIndex,
      [step.field]: completed,
    }

    // Check if all required steps are completed (excluding optional integration)
    if (stepIndex === steps.length - 1 || (stepIndex === steps.length - 2 && completed)) {
      const allCompleted = steps.slice(0, -1).every((s, idx) => {
        if (idx === stepIndex) return completed
        return progress[s.field]
      })

      if (allCompleted) {
        updates.is_completed = true
      }
    }

    try {
      const updated = await onboardingApi.updateProgress(updates)
      setProgress(updated)
    } catch (error) {
      console.error('Failed to update progress:', error)
    }
  }

  const handleNext = async () => {
    await updateStep(currentStep, true)
    
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      // Completed all steps
      if (onComplete) {
        onComplete()
      }
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSkip = async () => {
    if (currentStep === steps.length - 1) {
      // Skipping the last (optional) step completes onboarding
      await updateStep(currentStep, false)
      if (onComplete) {
        onComplete()
      }
    } else {
      handleNext()
    }
  }

  const handleClose = () => {
    if (onDismiss) {
      onDismiss()
    }
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <Card className="w-full max-w-2xl">
          <CardContent className="p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto" />
            <p className="mt-4 text-muted-foreground">Loading onboarding...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const CurrentStepComponent = steps[currentStep].component
  const isLastStep = currentStep === steps.length - 1
  const isOptional = isLastStep

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-4xl"
      >
        <Card>
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <div>
              <h2 className="text-2xl font-bold">Welcome to SoundHash</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Let&apos;s get you set up in just a few minutes
              </p>
            </div>
            <Button variant="ghost" size="icon" onClick={handleClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Progress indicator */}
          <div className="px-6 py-4 border-b">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">
                Step {currentStep + 1} of {steps.length}
              </span>
              <span className="text-sm text-muted-foreground">
                {Math.round(((currentStep + 1) / steps.length) * 100)}% Complete
              </span>
            </div>
            <div className="flex gap-2">
              {steps.map((step, idx) => (
                <div
                  key={step.id}
                  className="flex-1 h-2 bg-muted rounded-full overflow-hidden"
                >
                  <motion.div
                    className="h-full bg-primary"
                    initial={{ width: 0 }}
                    animate={{
                      width: idx < currentStep ? '100%' : idx === currentStep ? '50%' : '0%',
                    }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Steps sidebar */}
          <div className="flex">
            <div className="w-64 border-r p-6 space-y-2">
              {steps.map((step, idx) => (
                <button
                  key={step.id}
                  onClick={() => setCurrentStep(idx)}
                  className={`w-full flex items-start gap-3 p-3 rounded-lg text-left transition-colors ${
                    idx === currentStep
                      ? 'bg-primary/10 text-primary'
                      : idx < currentStep
                      ? 'text-muted-foreground hover:bg-muted'
                      : 'text-muted-foreground/50 cursor-not-allowed'
                  }`}
                  disabled={idx > currentStep}
                >
                  {progress && progress[step.field] ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                  ) : (
                    <Circle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm">{step.title}</div>
                    <div className="text-xs opacity-75 truncate">{step.description}</div>
                  </div>
                </button>
              ))}
            </div>

            {/* Content area */}
            <div className="flex-1 p-6">
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentStep}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="min-h-[400px] flex flex-col"
                >
                  <CurrentStepComponent progress={progress} onNext={handleNext} />
                </motion.div>
              </AnimatePresence>

              {/* Navigation buttons */}
              <div className="flex items-center justify-between mt-8 pt-6 border-t">
                <Button
                  variant="outline"
                  onClick={handlePrevious}
                  disabled={currentStep === 0}
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Previous
                </Button>

                <div className="flex gap-2">
                  {isOptional && (
                    <Button variant="ghost" onClick={handleSkip}>
                      Skip for now
                    </Button>
                  )}
                  <Button onClick={handleNext}>
                    {isLastStep ? 'Complete' : 'Next'}
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </motion.div>
    </div>
  )
}
