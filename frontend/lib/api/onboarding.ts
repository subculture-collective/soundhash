/**
 * API client for onboarding and tutorial system
 */

import api from '../api'
import type { OnboardingProgress, TutorialProgress, UserPreference, OnboardingStats } from '../types/onboarding'

export const onboardingApi = {
  // Onboarding Progress
  async getProgress(): Promise<OnboardingProgress> {
    const response = await api.get<OnboardingProgress>('/onboarding/progress')
    return response.data
  },

  async createProgress(data: Partial<OnboardingProgress>): Promise<OnboardingProgress> {
    const response = await api.post<OnboardingProgress>('/onboarding/progress', data)
    return response.data
  },

  async updateProgress(data: Partial<OnboardingProgress>): Promise<OnboardingProgress> {
    const response = await api.patch<OnboardingProgress>('/onboarding/progress', data)
    return response.data
  },

  // Tutorial Progress
  async listTutorials(): Promise<TutorialProgress[]> {
    const response = await api.get<TutorialProgress[]>('/onboarding/tutorials')
    return response.data
  },

  async getTutorial(tutorialId: string): Promise<TutorialProgress> {
    const response = await api.get<TutorialProgress>(`/onboarding/tutorials/${tutorialId}`)
    return response.data
  },

  async createTutorial(data: { tutorial_id: string; total_steps?: number }): Promise<TutorialProgress> {
    const response = await api.post<TutorialProgress>('/onboarding/tutorials', data)
    return response.data
  },

  async updateTutorial(
    tutorialId: string,
    data: Partial<TutorialProgress>
  ): Promise<TutorialProgress> {
    const response = await api.patch<TutorialProgress>(`/onboarding/tutorials/${tutorialId}`, data)
    return response.data
  },

  // User Preferences
  async getPreferences(): Promise<UserPreference> {
    const response = await api.get<UserPreference>('/onboarding/preferences')
    return response.data
  },

  async createPreferences(data: Partial<UserPreference>): Promise<UserPreference> {
    const response = await api.post<UserPreference>('/onboarding/preferences', data)
    return response.data
  },

  async updatePreferences(data: Partial<UserPreference>): Promise<UserPreference> {
    const response = await api.patch<UserPreference>('/onboarding/preferences', data)
    return response.data
  },

  // Statistics (Admin only)
  async getStats(): Promise<OnboardingStats> {
    const response = await api.get<OnboardingStats>('/onboarding/stats')
    return response.data
  },
}
