'use client'

import { Upload, Music } from 'lucide-react'
import { AudioUploader } from '@/components/features/audio/AudioUploader'
import { Card, CardContent } from '@/components/ui/card'
import type { OnboardingProgress } from '@/lib/types/onboarding'

interface FirstUploadStepProps {
  progress: OnboardingProgress | null
  onNext: () => void
}

export default function FirstUploadStep({ onNext }: FirstUploadStepProps) {
  const handleUploadComplete = () => {
    // Mark step as complete
    onNext()
  }

  return (
    <div className="flex flex-col h-full">
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Upload className="h-6 w-6 text-primary" />
          </div>
          <h3 className="text-2xl font-bold">Upload Your First Audio</h3>
        </div>
        <p className="text-muted-foreground">
          Let&apos;s try the audio fingerprinting in action
        </p>
      </div>

      <div className="space-y-4 mb-6">
        <Card>
          <CardContent className="p-6">
            <h4 className="font-semibold mb-3">What happens next:</h4>
            <ol className="space-y-2 text-sm">
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-semibold">
                  1
                </span>
                <span>Upload an audio or video file (mp3, wav, mp4, etc.)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-semibold">
                  2
                </span>
                <span>We&apos;ll extract an audio fingerprint</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-semibold">
                  3
                </span>
                <span>Search for matches across YouTube</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-semibold">
                  4
                </span>
                <span>Get detailed results with confidence scores</span>
              </li>
            </ol>
          </CardContent>
        </Card>

        <AudioUploader onUploadComplete={handleUploadComplete} />
      </div>

      <div className="mt-auto">
        <div className="flex items-start gap-3 p-4 bg-muted/50 rounded-lg">
          <Music className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-semibold mb-1">Supported formats</p>
            <p className="text-muted-foreground">
              MP3, WAV, MP4, M4A, OGG, FLAC, and more. Maximum file size: 100MB
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
