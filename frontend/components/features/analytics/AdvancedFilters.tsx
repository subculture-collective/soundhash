'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Filter, X, Calendar, Tag, Users } from 'lucide-react'

interface FilterState {
  dateRange: { start: string; end: string }
  eventTypes: string[]
  userSegments: string[]
  customFilters: { field: string; operator: string; value: string }[]
}

export function AdvancedFilters() {
  const [isOpen, setIsOpen] = useState(false)
  const [filters, setFilters] = useState<FilterState>({
    dateRange: { start: '', end: '' },
    eventTypes: [],
    userSegments: [],
    customFilters: [],
  })

  const eventTypes = [
    'page_view',
    'api_call',
    'upload',
    'match_found',
    'user_signup',
    'subscription_change',
  ]

  const userSegments = [
    'free_tier',
    'pro_tier',
    'enterprise',
    'trial',
    'active',
    'inactive',
  ]

  const toggleEventType = (type: string) => {
    setFilters((prev) => ({
      ...prev,
      eventTypes: prev.eventTypes.includes(type)
        ? prev.eventTypes.filter((t) => t !== type)
        : [...prev.eventTypes, type],
    }))
  }

  const toggleUserSegment = (segment: string) => {
    setFilters((prev) => ({
      ...prev,
      userSegments: prev.userSegments.includes(segment)
        ? prev.userSegments.filter((s) => s !== segment)
        : [...prev.userSegments, segment],
    }))
  }

  const addCustomFilter = () => {
    setFilters((prev) => ({
      ...prev,
      customFilters: [
        ...prev.customFilters,
        { field: '', operator: 'equals', value: '' },
      ],
    }))
  }

  const removeCustomFilter = (index: number) => {
    setFilters((prev) => ({
      ...prev,
      customFilters: prev.customFilters.filter((_, i) => i !== index),
    }))
  }

  const clearAllFilters = () => {
    setFilters({
      dateRange: { start: '', end: '' },
      eventTypes: [],
      userSegments: [],
      customFilters: [],
    })
  }

  const applyFilters = () => {
    console.log('Applying filters:', filters)
    // TODO: Implement filter application
    setIsOpen(false)
  }

  const activeFilterCount =
    (filters.dateRange.start ? 1 : 0) +
    filters.eventTypes.length +
    filters.userSegments.length +
    filters.customFilters.length

  return (
    <div className="space-y-4">
      {/* Filter Button */}
      <Button
        variant="outline"
        onClick={() => setIsOpen(!isOpen)}
        className="gap-2"
      >
        <Filter className="h-4 w-4" />
        Advanced Filters
        {activeFilterCount > 0 && (
          <span className="ml-1 rounded-full bg-blue-500 text-white text-xs px-2 py-0.5">
            {activeFilterCount}
          </span>
        )}
      </Button>

      {/* Filter Panel */}
      {isOpen && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Advanced Filters</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Date Range */}
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Date Range
              </label>
              <div className="grid gap-2 md:grid-cols-2">
                <div>
                  <label className="text-xs text-muted-foreground">From</label>
                  <Input
                    type="date"
                    value={filters.dateRange.start}
                    onChange={(e) =>
                      setFilters((prev) => ({
                        ...prev,
                        dateRange: { ...prev.dateRange, start: e.target.value },
                      }))
                    }
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground">To</label>
                  <Input
                    type="date"
                    value={filters.dateRange.end}
                    onChange={(e) =>
                      setFilters((prev) => ({
                        ...prev,
                        dateRange: { ...prev.dateRange, end: e.target.value },
                      }))
                    }
                  />
                </div>
              </div>
            </div>

            {/* Event Types */}
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <Tag className="h-4 w-4" />
                Event Types
              </label>
              <div className="flex flex-wrap gap-2">
                {eventTypes.map((type) => (
                  <Button
                    key={type}
                    variant={
                      filters.eventTypes.includes(type) ? 'default' : 'outline'
                    }
                    size="sm"
                    onClick={() => toggleEventType(type)}
                  >
                    {type.replace('_', ' ')}
                  </Button>
                ))}
              </div>
            </div>

            {/* User Segments */}
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <Users className="h-4 w-4" />
                User Segments
              </label>
              <div className="flex flex-wrap gap-2">
                {userSegments.map((segment) => (
                  <Button
                    key={segment}
                    variant={
                      filters.userSegments.includes(segment)
                        ? 'default'
                        : 'outline'
                    }
                    size="sm"
                    onClick={() => toggleUserSegment(segment)}
                  >
                    {segment.replace('_', ' ')}
                  </Button>
                ))}
              </div>
            </div>

            {/* Custom Filters */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Custom Filters</label>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={addCustomFilter}
                  className="gap-2"
                >
                  + Add Filter
                </Button>
              </div>
              {filters.customFilters.map((filter, index) => (
                <div key={index} className="flex gap-2">
                  <select className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm">
                    <option value="">Select field...</option>
                    <option value="user_id">User ID</option>
                    <option value="session_id">Session ID</option>
                    <option value="ip_address">IP Address</option>
                    <option value="referrer">Referrer</option>
                    <option value="user_agent">User Agent</option>
                  </select>
                  <select className="w-32 rounded-md border border-input bg-background px-3 py-2 text-sm">
                    <option value="equals">Equals</option>
                    <option value="contains">Contains</option>
                    <option value="starts_with">Starts with</option>
                    <option value="ends_with">Ends with</option>
                    <option value="not_equals">Not equals</option>
                  </select>
                  <Input className="flex-1" placeholder="Value..." />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeCustomFilter(index)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-4 border-t">
              <Button onClick={applyFilters} className="flex-1">
                Apply Filters
              </Button>
              <Button variant="outline" onClick={clearAllFilters}>
                Clear All
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
