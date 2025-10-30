'use client'

import { useState } from 'react'
import { Code, Book, ExternalLink, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import type { OnboardingProgress } from '@/lib/types/onboarding'

interface IntegrationStepProps {
  progress: OnboardingProgress | null
  onNext: () => void
}

export default function IntegrationStep({ progress, onNext }: IntegrationStepProps) {
  const [selectedSdk, setSelectedSdk] = useState<string | null>(null)

  const sdks = [
    {
      id: 'python',
      name: 'Python SDK',
      description: 'pip install soundhash',
      icon: '🐍',
      docsUrl: 'https://docs.soundhash.io/sdk/python',
    },
    {
      id: 'javascript',
      name: 'JavaScript SDK',
      description: 'npm install soundhash-js',
      icon: '📦',
      docsUrl: 'https://docs.soundhash.io/sdk/javascript',
    },
    {
      id: 'go',
      name: 'Go SDK',
      description: 'go get github.com/soundhash/go-sdk',
      icon: '🔷',
      docsUrl: 'https://docs.soundhash.io/sdk/go',
    },
    {
      id: 'rest',
      name: 'REST API',
      description: 'Direct HTTP requests',
      icon: '🌐',
      docsUrl: 'https://docs.soundhash.io/api',
    },
  ]

  const handleSelectSdk = (sdkId: string) => {
    setSelectedSdk(sdkId)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Code className="h-6 w-6 text-primary" />
          </div>
          <h3 className="text-2xl font-bold">Integration Setup</h3>
        </div>
        <p className="text-muted-foreground">
          Choose your preferred SDK or API method (optional)
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        {sdks.map((sdk) => (
          <Card
            key={sdk.id}
            className={`cursor-pointer transition-all ${
              selectedSdk === sdk.id
                ? 'ring-2 ring-primary bg-primary/5'
                : 'hover:border-primary/50'
            }`}
            onClick={() => handleSelectSdk(sdk.id)}
          >
            <CardContent className="p-4">
              <div className="flex flex-col h-full">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">{sdk.icon}</span>
                  {selectedSdk === sdk.id && (
                    <Check className="h-4 w-4 text-primary ml-auto" />
                  )}
                </div>
                <h4 className="font-semibold mb-1">{sdk.name}</h4>
                <p className="text-xs text-muted-foreground font-mono mb-3">
                  {sdk.description}
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full mt-auto gap-2"
                  onClick={(e) => {
                    e.stopPropagation()
                    window.open(sdk.docsUrl, '_blank')
                  }}
                >
                  <Book className="h-3 w-3" />
                  View Docs
                  <ExternalLink className="h-3 w-3" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {selectedSdk && (
        <Card className="mb-6">
          <CardContent className="p-4">
            <h4 className="font-semibold mb-2 text-sm">Quick Start</h4>
            <pre className="text-xs bg-muted p-3 rounded overflow-x-auto">
              <code>
                {selectedSdk === 'python' && `pip install soundhash

from soundhash import SoundHashClient

client = SoundHashClient(api_key="your_api_key")
result = client.fingerprint.create("audio.mp3")
print(result)`}
                {selectedSdk === 'javascript' && `npm install soundhash-js

import { SoundHashClient } from 'soundhash-js';

const client = new SoundHashClient('your_api_key');
const result = await client.fingerprints.create('audio.mp3');
console.log(result);`}
                {selectedSdk === 'go' && `go get github.com/soundhash/go-sdk

package main

import "github.com/soundhash/go-sdk"

func main() {
    client := soundhash.NewClient("your_api_key")
    result, _ := client.Fingerprints.Create("audio.mp3")
}`}
                {selectedSdk === 'rest' && `curl -X POST https://api.soundhash.io/v1/fingerprints \\
  -H "Authorization: Bearer your_api_key" \\
  -F "audio=@audio.mp3"`}
              </code>
            </pre>
          </CardContent>
        </Card>
      )}

      <div className="mt-auto space-y-4">
        <Card className="border-blue-500/50 bg-blue-500/5">
          <CardContent className="p-4">
            <div className="flex gap-3">
              <Book className="h-5 w-5 text-blue-500 flex-shrink-0" />
              <div className="text-sm">
                <p className="font-semibold text-blue-500 mb-1">Need help?</p>
                <p className="text-muted-foreground">
                  Check out our comprehensive documentation, code examples, and API reference
                  at docs.soundhash.io
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground">
            This step is optional. You can always integrate later from the documentation.
          </p>
        </div>
      </div>
    </div>
  )
}
