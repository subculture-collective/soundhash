'use client'

import { useState } from 'react'
import { Search, Book, MessageCircle, Mail, ExternalLink, ChevronRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

interface HelpArticle {
  id: string
  title: string
  category: string
  description: string
  url: string
}

export default function HelpCenter() {
  const [searchQuery, setSearchQuery] = useState('')

  const articles: HelpArticle[] = [
    {
      id: '1',
      title: 'Getting Started with SoundHash',
      category: 'Basics',
      description: 'Learn the fundamentals of audio fingerprinting',
      url: '/docs/getting-started',
    },
    {
      id: '2',
      title: 'Understanding Match Results',
      category: 'Features',
      description: 'How to interpret confidence scores and metadata',
      url: '/docs/match-results',
    },
    {
      id: '3',
      title: 'API Authentication',
      category: 'API',
      description: 'Setting up and managing API keys',
      url: '/docs/authentication',
    },
    {
      id: '4',
      title: 'Rate Limits and Quotas',
      category: 'API',
      description: 'Understanding usage limits and best practices',
      url: '/docs/rate-limits',
    },
    {
      id: '5',
      title: 'Supported Audio Formats',
      category: 'Features',
      description: 'Which file formats work with SoundHash',
      url: '/docs/audio-formats',
    },
    {
      id: '6',
      title: 'Troubleshooting Common Issues',
      category: 'Support',
      description: 'Solutions to frequently encountered problems',
      url: '/docs/troubleshooting',
    },
  ]

  const filteredArticles = articles.filter(
    (article) =>
      article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.category.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const categories = Array.from(new Set(articles.map((a) => a.category)))

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Help Center</h2>
        <p className="text-muted-foreground">
          Find answers to common questions and learn how to use SoundHash
        </p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search help articles..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Quick actions */}
      <div className="grid sm:grid-cols-3 gap-4">
        <Card className="cursor-pointer hover:border-primary/50 transition-colors">
          <CardContent className="p-6">
            <Book className="h-8 w-8 text-primary mb-3" />
            <h3 className="font-semibold mb-1">Documentation</h3>
            <p className="text-sm text-muted-foreground mb-3">
              Comprehensive guides and API reference
            </p>
            <Button variant="ghost" size="sm" className="gap-2 px-0">
              View Docs
              <ExternalLink className="h-3 w-3" />
            </Button>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:border-primary/50 transition-colors">
          <CardContent className="p-6">
            <MessageCircle className="h-8 w-8 text-primary mb-3" />
            <h3 className="font-semibold mb-1">Community</h3>
            <p className="text-sm text-muted-foreground mb-3">
              Join our Discord or Slack community
            </p>
            <Button variant="ghost" size="sm" className="gap-2 px-0">
              Join Chat
              <ExternalLink className="h-3 w-3" />
            </Button>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:border-primary/50 transition-colors">
          <CardContent className="p-6">
            <Mail className="h-8 w-8 text-primary mb-3" />
            <h3 className="font-semibold mb-1">Contact Support</h3>
            <p className="text-sm text-muted-foreground mb-3">
              Get help from our support team
            </p>
            <Button variant="ghost" size="sm" className="gap-2 px-0">
              Email Us
              <ExternalLink className="h-3 w-3" />
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Articles by category */}
      <div className="space-y-6">
        {categories.map((category) => {
          const categoryArticles = filteredArticles.filter((a) => a.category === category)
          
          if (categoryArticles.length === 0) return null

          return (
            <div key={category}>
              <h3 className="text-lg font-semibold mb-3">{category}</h3>
              <div className="space-y-2">
                {categoryArticles.map((article) => (
                  <Card
                    key={article.id}
                    className="cursor-pointer hover:border-primary/50 transition-colors"
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold mb-1">{article.title}</h4>
                          <p className="text-sm text-muted-foreground">{article.description}</p>
                        </div>
                        <ChevronRight className="h-5 w-5 text-muted-foreground flex-shrink-0 ml-4" />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )
        })}

        {filteredArticles.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No articles found matching your search</p>
          </div>
        )}
      </div>

      {/* Contact section */}
      <Card className="border-primary/50 bg-primary/5">
        <CardContent className="p-6">
          <h3 className="font-semibold mb-2">Still need help?</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Can&apos;t find what you&apos;re looking for? Our support team is here to help.
          </p>
          <div className="flex gap-2">
            <Button variant="outline">
              <MessageCircle className="h-4 w-4 mr-2" />
              Chat with us
            </Button>
            <Button variant="outline">
              <Mail className="h-4 w-4 mr-2" />
              Email support
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
