'use client'

import { useState, useEffect, useRef } from 'react'
import { HelpCircle, X } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface ContextualTooltipProps {
  title: string
  content: string
  position?: 'top' | 'bottom' | 'left' | 'right'
  show?: boolean
  onClose?: () => void
}

export default function ContextualTooltip({
  title,
  content,
  position = 'top',
  show = true,
  onClose,
}: ContextualTooltipProps) {
  const [isVisible, setIsVisible] = useState(show)
  const tooltipRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setIsVisible(show)
  }, [show])

  const handleClose = () => {
    setIsVisible(false)
    if (onClose) {
      onClose()
    }
  }

  if (!isVisible) return null

  const positionClasses = {
    top: 'bottom-full mb-2',
    bottom: 'top-full mt-2',
    left: 'right-full mr-2',
    right: 'left-full ml-2',
  }

  return (
    <div className="relative inline-block">
      <HelpCircle className="h-5 w-5 text-primary cursor-help" />
      
      <div
        ref={tooltipRef}
        className={`absolute z-50 ${positionClasses[position]} w-72`}
      >
        <Card className="shadow-lg border-primary/50">
          <CardContent className="p-4">
            <div className="flex items-start justify-between gap-2 mb-2">
              <h4 className="font-semibold text-sm">{title}</h4>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 -mt-1 -mr-1"
                onClick={handleClose}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">{content}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Hook for managing contextual help
export function useContextualHelp() {
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null)
  const [dismissedTooltips, setDismissedTooltips] = useState<Set<string>>(new Set())

  useEffect(() => {
    // Load dismissed tooltips from localStorage
    const stored = localStorage.getItem('dismissedTooltips')
    if (stored) {
      setDismissedTooltips(new Set(JSON.parse(stored)))
    }
  }, [])

  const showTooltip = (tooltipId: string) => {
    if (!dismissedTooltips.has(tooltipId)) {
      setActiveTooltip(tooltipId)
    }
  }

  const hideTooltip = () => {
    setActiveTooltip(null)
  }

  const dismissTooltip = (tooltipId: string) => {
    const updated = new Set(dismissedTooltips)
    updated.add(tooltipId)
    setDismissedTooltips(updated)
    localStorage.setItem('dismissedTooltips', JSON.stringify(Array.from(updated)))
    hideTooltip()
  }

  const isTooltipVisible = (tooltipId: string) => {
    return activeTooltip === tooltipId && !dismissedTooltips.has(tooltipId)
  }

  return {
    showTooltip,
    hideTooltip,
    dismissTooltip,
    isTooltipVisible,
  }
}
