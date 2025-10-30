'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

interface TourStep {
  target: string
  title: string
  content: string
  placement?: 'top' | 'bottom' | 'left' | 'right'
}

interface ProductTourProps {
  steps: TourStep[]
  onComplete?: () => void
  onSkip?: () => void
}

export default function ProductTour({ steps, onComplete, onSkip }: ProductTourProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [targetElement, setTargetElement] = useState<HTMLElement | null>(null)
  const [position, setPosition] = useState({ top: 0, left: 0 })

  useEffect(() => {
    const step = steps[currentStep]
    if (!step) return

    const element = document.querySelector(step.target) as HTMLElement
    if (!element) return

    // Use requestAnimationFrame to avoid synchronous state updates
    requestAnimationFrame(() => {
      setTargetElement(element)
      
      // Scroll element into view
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      
      // Highlight element
      element.style.position = 'relative'
      element.style.zIndex = '9999'
      
      // Calculate tooltip position
      const rect = element.getBoundingClientRect()
      const placement = step.placement || 'bottom'
      
      let top = 0
      let left = 0
      
      switch (placement) {
        case 'top':
          top = rect.top - 20
          left = rect.left + rect.width / 2
          break
        case 'bottom':
          top = rect.bottom + 20
          left = rect.left + rect.width / 2
          break
        case 'left':
          top = rect.top + rect.height / 2
          left = rect.left - 20
          break
        case 'right':
          top = rect.top + rect.height / 2
          left = rect.right + 20
          break
      }
      
      setPosition({ top, left })
    })

    return () => {
      if (element) {
        element.style.position = ''
        element.style.zIndex = ''
      }
    }
  }, [currentStep, steps])

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      handleComplete()
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleComplete = () => {
    if (onComplete) {
      onComplete()
    }
  }

  const handleSkip = () => {
    if (onSkip) {
      onSkip()
    }
  }

  if (!steps.length) return null

  const step = steps[currentStep]
  const isLastStep = currentStep === steps.length - 1

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50 z-[9998]" onClick={handleSkip} />

      {/* Spotlight effect on target */}
      {targetElement && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed z-[9999] pointer-events-none"
          style={{
            top: targetElement.getBoundingClientRect().top - 8,
            left: targetElement.getBoundingClientRect().left - 8,
            width: targetElement.getBoundingClientRect().width + 16,
            height: targetElement.getBoundingClientRect().height + 16,
            boxShadow: '0 0 0 4px rgba(59, 130, 246, 0.5), 0 0 0 9999px rgba(0, 0, 0, 0.5)',
            borderRadius: '8px',
          }}
        />
      )}

      {/* Tooltip */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="fixed z-[10000] w-96"
          style={{
            top: position.top,
            left: position.left,
            transform: 'translate(-50%, 0)',
          }}
        >
          <Card>
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h4 className="font-semibold text-lg mb-1">{step.title}</h4>
                  <p className="text-sm text-muted-foreground">{step.content}</p>
                </div>
                <Button variant="ghost" size="icon" onClick={handleSkip}>
                  <X className="h-4 w-4" />
                </Button>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex gap-1">
                  {steps.map((_, idx) => (
                    <div
                      key={idx}
                      className={`h-1.5 w-6 rounded-full transition-colors ${
                        idx === currentStep ? 'bg-primary' : 'bg-muted'
                      }`}
                    />
                  ))}
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handlePrevious}
                    disabled={currentStep === 0}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button size="sm" onClick={handleNext}>
                    {isLastStep ? 'Finish' : 'Next'}
                    {!isLastStep && <ChevronRight className="h-4 w-4 ml-1" />}
                  </Button>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t">
                <p className="text-xs text-muted-foreground text-center">
                  Step {currentStep + 1} of {steps.length}
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </AnimatePresence>
    </>
  )
}
