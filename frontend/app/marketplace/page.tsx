'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Search, Star, Download, Filter, Package, Palette, Plug, Database } from 'lucide-react'

interface MarketplaceItem {
  id: number
  title: string
  description: string
  item_type: string
  category: string
  price: number
  currency: string
  version: string
  purchase_count: number
  average_rating: number
  review_count: number
  preview_url?: string
  tags?: string[]
}

export default function MarketplacePage() {
  const [items, setItems] = useState<MarketplaceItem[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedType, setSelectedType] = useState<string | null>(null)

  // Mock data for demo
  useEffect(() => {
    // In production, this would fetch from API
    const mockItems: MarketplaceItem[] = [
      {
        id: 1,
        title: 'EDM Fingerprint Database',
        description: 'Comprehensive electronic dance music fingerprint database with over 500k tracks',
        item_type: 'fingerprint_db',
        category: 'Music',
        price: 9900,
        currency: 'usd',
        version: '2.1.0',
        purchase_count: 234,
        average_rating: 4.8,
        review_count: 45,
        tags: ['edm', 'electronic', 'dance'],
      },
      {
        id: 2,
        title: 'Advanced Spectral Analyzer',
        description: 'Enhanced audio analysis plugin with ML-powered pattern recognition',
        item_type: 'plugin',
        category: 'Tools',
        price: 4900,
        currency: 'usd',
        version: '1.5.2',
        purchase_count: 189,
        average_rating: 4.6,
        review_count: 32,
        tags: ['analysis', 'ml', 'audio'],
      },
      {
        id: 3,
        title: 'Dark Pro Theme',
        description: 'Professional dark theme with customizable accent colors for white-label deployments',
        item_type: 'theme',
        category: 'Themes',
        price: 2900,
        currency: 'usd',
        version: '1.0.1',
        purchase_count: 567,
        average_rating: 4.9,
        review_count: 98,
        tags: ['dark', 'professional', 'ui'],
      },
      {
        id: 4,
        title: 'Spotify Integration Pack',
        description: 'Pre-built connector for seamless Spotify API integration',
        item_type: 'integration',
        category: 'Integrations',
        price: 3900,
        currency: 'usd',
        version: '2.0.0',
        purchase_count: 421,
        average_rating: 4.7,
        review_count: 76,
        tags: ['spotify', 'api', 'streaming'],
      },
    ]
    
    setTimeout(() => {
      setItems(mockItems)
      setLoading(false)
    }, 500)
  }, [])

  const getItemTypeIcon = (type: string) => {
    switch (type) {
      case 'fingerprint_db':
        return <Database className="h-5 w-5" />
      case 'plugin':
        return <Plug className="h-5 w-5" />
      case 'theme':
        return <Palette className="h-5 w-5" />
      case 'integration':
        return <Package className="h-5 w-5" />
      default:
        return <Package className="h-5 w-5" />
    }
  }

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase(),
    }).format(price / 100)
  }

  const filteredItems = items.filter((item) => {
    const matchesSearch = !searchQuery || 
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = !selectedType || item.item_type === selectedType
    return matchesSearch && matchesType
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Community Marketplace</h1>
          <p className="text-muted-foreground">
            Discover plugins, databases, themes, and integrations from the community
          </p>
        </div>

        {/* Stats Banner */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Items</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{items.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Creators</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">156</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Downloads</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">12.5K</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Avg Rating</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold flex items-center gap-1">
                4.8 <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search and Filters */}
        <div className="mb-6 space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  placeholder="Search marketplace..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Button variant="outline">
              <Filter className="h-4 w-4 mr-2" />
              Filters
            </Button>
          </div>

          {/* Category Filters */}
          <div className="flex gap-2 flex-wrap">
            <Button
              variant={selectedType === null ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedType(null)}
            >
              All
            </Button>
            <Button
              variant={selectedType === 'fingerprint_db' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedType('fingerprint_db')}
            >
              <Database className="h-4 w-4 mr-1" />
              Databases
            </Button>
            <Button
              variant={selectedType === 'plugin' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedType('plugin')}
            >
              <Plug className="h-4 w-4 mr-1" />
              Plugins
            </Button>
            <Button
              variant={selectedType === 'theme' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedType('theme')}
            >
              <Palette className="h-4 w-4 mr-1" />
              Themes
            </Button>
            <Button
              variant={selectedType === 'integration' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedType('integration')}
            >
              <Package className="h-4 w-4 mr-1" />
              Integrations
            </Button>
          </div>
        </div>

        {/* Items Grid */}
        {loading ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">Loading marketplace items...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredItems.map((item) => (
              <Card key={item.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getItemTypeIcon(item.item_type)}
                      <Badge variant="secondary">{item.item_type.replace('_', ' ')}</Badge>
                    </div>
                    <span className="text-lg font-bold">{formatPrice(item.price, item.currency)}</span>
                  </div>
                  <CardTitle className="text-xl">{item.title}</CardTitle>
                  <CardDescription className="line-clamp-2">{item.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                        <span className="font-medium">{item.average_rating}</span>
                        <span>({item.review_count})</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Download className="h-4 w-4" />
                        <span>{item.purchase_count}</span>
                      </div>
                    </div>
                    {item.tags && (
                      <div className="flex gap-1 flex-wrap">
                        {item.tags.map((tag) => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                    <p className="text-xs text-muted-foreground">Version {item.version}</p>
                  </div>
                </CardContent>
                <CardFooter className="flex gap-2">
                  <Button className="flex-1">Purchase</Button>
                  <Button variant="outline">Preview</Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}

        {filteredItems.length === 0 && !loading && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No items found matching your criteria.</p>
          </div>
        )}
      </div>
    </div>
  )
}
