'use client'

import { useState } from 'react'
import { Key, Copy, Check, Eye, EyeOff, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import type { OnboardingProgress } from '@/lib/types/onboarding'

interface ApiKeyStepProps {
  progress: OnboardingProgress | null
  onNext: () => void
}

export default function ApiKeyStep(_props: ApiKeyStepProps) {
  const [apiKey, setApiKey] = useState<string>('')
  const [showKey, setShowKey] = useState(false)
  const [copied, setCopied] = useState(false)
  const [generated, setGenerated] = useState(false)

  const generateApiKey = () => {
    // In a real implementation, this would call the API
    const mockKey = `sh_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`
    setApiKey(mockKey)
    setGenerated(true)
  }

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(apiKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Key className="h-6 w-6 text-primary" />
          </div>
          <h3 className="text-2xl font-bold">Generate Your API Key</h3>
        </div>
        <p className="text-muted-foreground">
          Your API key is used to authenticate requests to the SoundHash API
        </p>
      </div>

      {!generated ? (
        <div className="space-y-6">
          <Card>
            <CardContent className="p-6">
              <h4 className="font-semibold mb-3">What you&apos;ll be able to do:</h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <Check className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>Upload and process audio files</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>Search for matches across YouTube</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>Access detailed analytics and reports</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>Integrate with your applications</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          <Button
            onClick={generateApiKey}
            size="lg"
            className="w-full"
          >
            <Key className="h-4 w-4 mr-2" />
            Generate API Key
          </Button>
        </div>
      ) : (
        <div className="space-y-6">
          <Card className="border-green-500/50 bg-green-500/5">
            <CardContent className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <Check className="h-5 w-5 text-green-500" />
                <h4 className="font-semibold text-green-500">API Key Generated!</h4>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                Your API key has been generated. Make sure to save it somewhere safe – you won&apos;t
                be able to see it again!
              </p>
              
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <Input
                    type={showKey ? 'text' : 'password'}
                    value={apiKey}
                    readOnly
                    className="font-mono pr-10"
                  />
                  <button
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-muted rounded"
                  >
                    {showKey ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
                <Button
                  variant="outline"
                  onClick={copyToClipboard}
                  className="gap-2"
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="border-amber-500/50 bg-amber-500/5">
            <CardContent className="p-4">
              <div className="flex gap-3">
                <AlertCircle className="h-5 w-5 text-amber-500 flex-shrink-0" />
                <div className="text-sm">
                  <p className="font-semibold text-amber-500 mb-1">Keep your key secure</p>
                  <p className="text-muted-foreground">
                    Never share your API key publicly or commit it to version control. You can
                    regenerate it anytime from your account settings.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="bg-muted rounded-lg p-4">
            <h4 className="font-semibold mb-2 text-sm">Quick example:</h4>
            <pre className="text-xs bg-background p-3 rounded overflow-x-auto">
              <code>{`curl -X POST https://api.soundhash.io/v1/fingerprints \\
  -H "Authorization: Bearer ${apiKey.substring(0, 20)}..." \\
  -F "audio=@audio.mp3"`}</code>
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
