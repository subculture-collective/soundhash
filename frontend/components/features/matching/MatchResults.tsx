'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Clock, TrendingUp, Play, Pause } from 'lucide-react'
import { formatTime } from '@/lib/utils'
import { useState } from 'react'

interface Match {
  id: string
  title: string
  channel_name: string
  video_url: string
  confidence: number
  start_time: number
  end_time: number
  view_count?: number
  thumbnail_url?: string
  audio_url?: string
}

interface MatchResultsProps {
  matches: Match[]
  loading?: boolean
}

export function MatchResults({ matches, loading = false }: MatchResultsProps) {
  const [playingId, setPlayingId] = useState<string | null>(null)

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
        <p className="mt-4 text-muted-foreground">Searching for matches...</p>
      </div>
    )
  }

  if (matches.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-lg text-muted-foreground">No matches found</p>
        <p className="text-sm text-muted-foreground mt-2">
          Try uploading a different audio clip
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">
          Found {matches.length} {matches.length === 1 ? 'match' : 'matches'}
        </h2>
        <p className="text-muted-foreground">
          Results are sorted by confidence score
        </p>
      </div>

      <div className="space-y-4">
        {matches.map((match) => (
          <Card key={match.id} className="overflow-hidden hover:shadow-lg transition-shadow">
            <div className="flex flex-col md:flex-row">
              {/* Thumbnail */}
              {match.thumbnail_url && (
                <div className="relative w-full md:w-48 h-32 md:h-auto bg-muted flex-shrink-0">
                  <img
                    src={match.thumbnail_url}
                    alt={match.title}
                    className="w-full h-full object-cover"
                  />
                  {match.audio_url && (
                    <button
                      onClick={() => setPlayingId(playingId === match.id ? null : match.id)}
                      className="absolute inset-0 flex items-center justify-center bg-black/30 hover:bg-black/50 transition-colors"
                    >
                      {playingId === match.id ? (
                        <Pause className="w-12 h-12 text-white" />
                      ) : (
                        <Play className="w-12 h-12 text-white" />
                      )}
                    </button>
                  )}
                </div>
              )}

              {/* Content */}
              <div className="flex-1 p-6">
                <CardHeader className="p-0 mb-4">
                  <CardTitle className="text-xl">{match.title}</CardTitle>
                </CardHeader>

                <CardContent className="p-0 space-y-4">
                  {/* Stats */}
                  <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <TrendingUp className="w-4 h-4 text-green-500" />
                      <span className="font-medium text-foreground">
                        {(match.confidence * 100).toFixed(1)}%
                      </span>
                      <span>match</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      <span>
                        {formatTime(match.start_time)} - {formatTime(match.end_time)}
                      </span>
                    </div>
                  </div>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary">{match.channel_name}</Badge>
                    {match.view_count && (
                      <Badge variant="outline">
                        {match.view_count.toLocaleString()} views
                      </Badge>
                    )}
                  </div>

                  {/* Action Button */}
                  <div>
                    <Button asChild className="gap-2">
                      <a
                        href={match.video_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Watch Video
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    </Button>
                  </div>
                </CardContent>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
