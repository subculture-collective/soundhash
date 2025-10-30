import { ReactNode } from 'react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface MetricCardProps {
  icon: ReactNode
  title: string
  value: string | number
  change?: number
  changeLabel?: string
  variant?: 'default' | 'danger' | 'success'
}

export function MetricCard({ 
  icon, 
  title, 
  value, 
  change, 
  changeLabel,
  variant = 'default' 
}: MetricCardProps) {
  const isPositive = change && change > 0
  const isNegative = change && change < 0

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="text-sm font-medium text-muted-foreground">{title}</div>
        <div className={cn(
          'text-muted-foreground',
          variant === 'danger' && 'text-red-500',
          variant === 'success' && 'text-green-500'
        )}>
          {icon}
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change !== undefined && (
          <p className="text-xs text-muted-foreground mt-1">
            <span className={cn(
              isPositive && 'text-green-600',
              isNegative && 'text-red-600'
            )}>
              {isPositive && '+'}{change}%
            </span>
            {changeLabel && ` ${changeLabel}`}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
