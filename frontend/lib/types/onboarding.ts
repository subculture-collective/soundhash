/**
 * Types for onboarding and tutorial system
 */

export interface OnboardingProgress {
  id: number
  user_id: number
  is_completed: boolean
  current_step: number
  use_case: 'content_creator' | 'developer' | 'enterprise' | null
  
  // Milestone tracking
  welcome_completed: boolean
  use_case_selected: boolean
  api_key_generated: boolean
  first_upload_completed: boolean
  dashboard_explored: boolean
  integration_started: boolean
  
  // Tour tracking
  tour_completed: boolean
  tour_dismissed: boolean
  tour_last_step: number
  
  // Sample data
  sample_data_generated: boolean
  
  // Metadata
  custom_data: Record<string, unknown> | null
  started_at: string
  completed_at: string | null
  created_at: string
  updated_at: string | null
}

export interface TutorialProgress {
  id: number
  user_id: number
  tutorial_id: string
  is_completed: boolean
  progress_percent: number
  current_step: number
  total_steps: number | null
  started_at: string
  completed_at: string | null
  last_viewed_at: string
}

export interface UserPreference {
  id: number
  user_id: number
  show_tooltips: boolean
  show_contextual_help: boolean
  auto_start_tours: boolean
  show_onboarding_tips: boolean
  daily_tips_enabled: boolean
  theme: string
  language: string
  timezone: string | null
  beta_features_enabled: boolean
  preferences_data: Record<string, unknown> | null
  created_at: string
  updated_at: string | null
}

export interface OnboardingStats {
  total_users: number
  completed_users: number
  completion_rate: number
  avg_completion_time_minutes: number | null
  step_completion_rates: Record<string, number>
  use_case_distribution: Record<string, number>
}

export interface OnboardingStep {
  id: number
  title: string
  description: string
  icon: string
  completed: boolean
  required: boolean
  estimatedTime: string
}

export interface Tutorial {
  id: string
  title: string
  description: string
  category: string
  duration: string
  thumbnail: string
  video_url?: string
  steps: TutorialStep[]
  tags: string[]
}

export interface TutorialStep {
  id: number
  title: string
  content: string
  action?: string
  target?: string
}

export interface ProductTourStep {
  target: string
  title: string
  content: string
  placement?: 'top' | 'bottom' | 'left' | 'right'
  disableBeacon?: boolean
  spotlightClicks?: boolean
}

export interface QuickStartTemplate {
  id: string
  name: string
  description: string
  category: string
  icon: string
  config: Record<string, unknown>
}
