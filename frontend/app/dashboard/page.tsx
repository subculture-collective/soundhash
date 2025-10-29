'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AudioUploader } from '@/components/features/audio/AudioUploader'
import { MatchResults } from '@/components/features/matching/MatchResults'
import { useState } from 'react'
import { FileAudio, Search, TrendingUp, Clock } from 'lucide-react'

export default function DashboardPage() {
  const [matches, setMatches] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const handleUploadComplete = (data: any) => {
    console.log('Upload complete:', data)
    // In a real app, this would trigger the matching process
    setLoading(true)
    // Simulate API call
    setTimeout(() => {
      setMatches([])
      setLoading(false)
    }, 2000)
  }

  // Mock stats data
  const stats = {
    total_uploads: 42,
    total_matches: 38,
    success_rate: 90.5,
    avg_confidence: 87.3,
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Dashboard</h1>
          <p className="text-muted-foreground">
            Upload audio clips and find their sources across the web
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Uploads</CardTitle>
              <FileAudio className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_uploads}</div>
              <p className="text-xs text-muted-foreground">
                +4 from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Matches Found</CardTitle>
              <Search className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_matches}</div>
              <p className="text-xs text-muted-foreground">
                +8% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.success_rate}%</div>
              <p className="text-xs text-muted-foreground">
                Above average
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.avg_confidence}%</div>
              <p className="text-xs text-muted-foreground">
                High accuracy
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Upload Section */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Upload Audio</CardTitle>
            <CardDescription>
              Upload an audio or video file to find matching sources
            </CardDescription>
          </CardHeader>
          <CardContent>
            <AudioUploader onUploadComplete={handleUploadComplete} />
          </CardContent>
        </Card>

        {/* Results Section */}
        {(loading || matches.length > 0) && (
          <Card>
            <CardHeader>
              <CardTitle>Match Results</CardTitle>
              <CardDescription>
                Audio clips that match your upload
              </CardDescription>
            </CardHeader>
            <CardContent>
              <MatchResults matches={matches} loading={loading} />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
