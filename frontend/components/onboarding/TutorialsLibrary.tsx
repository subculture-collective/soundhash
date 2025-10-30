'use client'

import { useState } from 'react'
import { Play, Clock, CheckCircle, Filter } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface Tutorial {
  id: string
  title: string
  description: string
  duration: string
  category: string
  thumbnail: string
  completed: boolean
  tags: string[]
}

interface TutorialsLibraryProps {
  onSelectTutorial?: (tutorialId: string) => void
}

export default function TutorialsLibrary({ onSelectTutorial }: TutorialsLibraryProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  const tutorials: Tutorial[] = [
    {
      id: 'getting-started',
      title: 'Getting Started with SoundHash',
      description: 'Learn the basics of audio fingerprinting and how to use the platform',
      duration: '5:30',
      category: 'Basics',
      thumbnail: '/tutorials/getting-started.jpg',
      completed: false,
      tags: ['beginner', 'overview'],
    },
    {
      id: 'api-quickstart',
      title: 'API Quick Start Guide',
      description: 'Make your first API request and understand the response format',
      duration: '8:15',
      category: 'API',
      thumbnail: '/tutorials/api-quickstart.jpg',
      completed: false,
      tags: ['api', 'development'],
    },
    {
      id: 'uploading-audio',
      title: 'Uploading and Processing Audio',
      description: 'Best practices for uploading audio files and managing fingerprints',
      duration: '6:45',
      category: 'Features',
      thumbnail: '/tutorials/uploading.jpg',
      completed: true,
      tags: ['audio', 'upload'],
    },
    {
      id: 'understanding-matches',
      title: 'Understanding Match Results',
      description: 'How to interpret confidence scores and match metadata',
      duration: '7:20',
      category: 'Features',
      thumbnail: '/tutorials/matches.jpg',
      completed: false,
      tags: ['matching', 'analysis'],
    },
    {
      id: 'python-sdk',
      title: 'Using the Python SDK',
      description: 'Integrate SoundHash into your Python applications',
      duration: '12:00',
      category: 'SDKs',
      thumbnail: '/tutorials/python-sdk.jpg',
      completed: false,
      tags: ['python', 'sdk', 'integration'],
    },
    {
      id: 'advanced-search',
      title: 'Advanced Search Techniques',
      description: 'Optimize your searches and filter results effectively',
      duration: '9:30',
      category: 'Advanced',
      thumbnail: '/tutorials/advanced-search.jpg',
      completed: false,
      tags: ['advanced', 'search'],
    },
  ]

  const categories = ['all', ...Array.from(new Set(tutorials.map((t) => t.category)))]

  const filteredTutorials =
    selectedCategory === 'all'
      ? tutorials
      : tutorials.filter((t) => t.category === selectedCategory)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Video Tutorials</h2>
          <p className="text-muted-foreground mt-1">
            Learn at your own pace with our comprehensive video library
          </p>
        </div>
      </div>

      {/* Category filter */}
      <div className="flex gap-2 flex-wrap">
        {categories.map((category) => (
          <Button
            key={category}
            variant={selectedCategory === category ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedCategory(category)}
          >
            <Filter className="h-3 w-3 mr-2" />
            {category.charAt(0).toUpperCase() + category.slice(1)}
          </Button>
        ))}
      </div>

      {/* Tutorial grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTutorials.map((tutorial) => (
          <Card
            key={tutorial.id}
            className="cursor-pointer hover:border-primary/50 transition-all group"
            onClick={() => onSelectTutorial?.(tutorial.id)}
          >
            <CardContent className="p-0">
              {/* Thumbnail */}
              <div className="relative aspect-video bg-muted rounded-t-lg overflow-hidden">
                {/* Placeholder for thumbnail */}
                <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-purple-500/20 flex items-center justify-center">
                  <Play className="h-12 w-12 text-white/80 group-hover:scale-110 transition-transform" />
                </div>
                
                {/* Duration badge */}
                <div className="absolute bottom-2 right-2 bg-black/80 text-white px-2 py-1 rounded text-xs flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {tutorial.duration}
                </div>

                {/* Completed badge */}
                {tutorial.completed && (
                  <div className="absolute top-2 right-2 bg-green-500 text-white p-1 rounded-full">
                    <CheckCircle className="h-4 w-4" />
                  </div>
                )}
              </div>

              {/* Content */}
              <div className="p-4">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-semibold line-clamp-2 group-hover:text-primary transition-colors">
                    {tutorial.title}
                  </h3>
                </div>
                
                <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                  {tutorial.description}
                </p>

                {/* Tags */}
                <div className="flex flex-wrap gap-1">
                  <Badge variant="secondary" className="text-xs">
                    {tutorial.category}
                  </Badge>
                  {tutorial.tags.slice(0, 2).map((tag) => (
                    <Badge key={tag} variant="outline" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredTutorials.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No tutorials found in this category</p>
        </div>
      )}
    </div>
  )
}
