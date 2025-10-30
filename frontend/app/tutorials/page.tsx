'use client'

import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import TutorialsLibrary from '@/components/onboarding/TutorialsLibrary'
import QuickStartTemplates from '@/components/onboarding/QuickStartTemplates'
import HelpCenter from '@/components/onboarding/HelpCenter'

export default function TutorialsPage() {
  const [selectedTutorial, setSelectedTutorial] = useState<string | null>(null)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Learning Resources</h1>
          <p className="text-muted-foreground">
            Everything you need to master SoundHash
          </p>
        </div>

        <Tabs defaultValue="tutorials" className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-3">
            <TabsTrigger value="tutorials">Video Tutorials</TabsTrigger>
            <TabsTrigger value="templates">Templates</TabsTrigger>
            <TabsTrigger value="help">Help Center</TabsTrigger>
          </TabsList>

          <TabsContent value="tutorials">
            <TutorialsLibrary onSelectTutorial={setSelectedTutorial} />
          </TabsContent>

          <TabsContent value="templates">
            <QuickStartTemplates />
          </TabsContent>

          <TabsContent value="help">
            <HelpCenter />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
