'use client'

import { useState } from 'react'
import { FileCode, Sparkles, Zap, Copy, Check } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface Template {
  id: string
  name: string
  description: string
  category: string
  icon: string
  language: string
  code: string
}

export default function QuickStartTemplates() {
  const [selectedTemplate, setSelectedTemplate] = useState<string>('python-basic')
  const [copied, setCopied] = useState(false)

  const templates: Template[] = [
    {
      id: 'python-basic',
      name: 'Python - Basic Upload',
      description: 'Upload and fingerprint an audio file',
      category: 'Getting Started',
      icon: '🐍',
      language: 'python',
      code: `from soundhash import SoundHashClient

# Initialize client
client = SoundHashClient(api_key="your_api_key")

# Upload and fingerprint audio
result = client.fingerprints.create("path/to/audio.mp3")

# Get matches
matches = client.matches.search(result.fingerprint_id)

# Print results
for match in matches:
    print(f"Match: {match.video_title}")
    print(f"Confidence: {match.confidence}%")`,
    },
    {
      id: 'python-batch',
      name: 'Python - Batch Processing',
      description: 'Process multiple files efficiently',
      category: 'Advanced',
      icon: '🐍',
      language: 'python',
      code: `from soundhash import SoundHashClient
import os
from concurrent.futures import ThreadPoolExecutor

client = SoundHashClient(api_key="your_api_key")

def process_audio(file_path):
    result = client.fingerprints.create(file_path)
    matches = client.matches.search(result.fingerprint_id)
    return {
        'file': file_path,
        'matches': len(matches),
        'top_match': matches[0] if matches else None
    }

# Process all files in directory
audio_dir = "audio_files/"
files = [os.path.join(audio_dir, f) for f in os.listdir(audio_dir)]

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(process_audio, files))

for result in results:
    print(f"{result['file']}: {result['matches']} matches")`,
    },
    {
      id: 'javascript-basic',
      name: 'JavaScript - Basic Upload',
      description: 'Upload audio in Node.js or browser',
      category: 'Getting Started',
      icon: '📦',
      language: 'javascript',
      code: `import { SoundHashClient } from 'soundhash-js';

// Initialize client
const client = new SoundHashClient('your_api_key');

// Upload and fingerprint audio
async function processAudio() {
  const result = await client.fingerprints.create('audio.mp3');
  
  // Get matches
  const matches = await client.matches.search(result.fingerprintId);
  
  // Display results
  matches.forEach(match => {
    console.log(\`Match: \${match.videoTitle}\`);
    console.log(\`Confidence: \${match.confidence}%\`);
  });
}

processAudio().catch(console.error);`,
    },
    {
      id: 'curl-basic',
      name: 'cURL - Direct API',
      description: 'Make requests with cURL',
      category: 'Getting Started',
      icon: '🌐',
      language: 'bash',
      code: `# Upload audio file
curl -X POST https://api.soundhash.io/v1/fingerprints \\
  -H "Authorization: Bearer your_api_key" \\
  -F "audio=@audio.mp3"

# Response: { "fingerprint_id": "fp_123...", ... }

# Search for matches
curl -X GET https://api.soundhash.io/v1/matches/fp_123... \\
  -H "Authorization: Bearer your_api_key"

# Response: { "matches": [...], "total": 5 }`,
    },
    {
      id: 'python-streaming',
      name: 'Python - Real-time Streaming',
      description: 'Process audio streams in real-time',
      category: 'Advanced',
      icon: '🐍',
      language: 'python',
      code: `from soundhash import SoundHashClient
import pyaudio

client = SoundHashClient(api_key="your_api_key")

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

p = pyaudio.PyAudio()

# Open stream
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK
)

print("Listening...")

try:
    while True:
        # Read audio chunk
        data = stream.read(CHUNK)
        
        # Process chunk
        result = client.streaming.process_chunk(data)
        
        if result.matches:
            print(f"Match found: {result.matches[0].video_title}")
except KeyboardInterrupt:
    stream.stop_stream()
    stream.close()
    p.terminate()`,
    },
  ]

  const currentTemplate = templates.find((t) => t.id === selectedTemplate)

  const handleCopy = async () => {
    if (currentTemplate) {
      await navigator.clipboard.writeText(currentTemplate.code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Quick Start Templates</h2>
        <p className="text-muted-foreground">
          Get started quickly with pre-built code examples
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Template list */}
        <div className="lg:col-span-1 space-y-2">
          {templates.map((template) => (
            <Card
              key={template.id}
              className={`cursor-pointer transition-all ${
                selectedTemplate === template.id
                  ? 'ring-2 ring-primary bg-primary/5'
                  : 'hover:border-primary/50'
              }`}
              onClick={() => setSelectedTemplate(template.id)}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <span className="text-2xl flex-shrink-0">{template.icon}</span>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-sm mb-1">{template.name}</h4>
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {template.description}
                    </p>
                    <Badge variant="secondary" className="text-xs mt-2">
                      {template.category}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Code display */}
        <div className="lg:col-span-2">
          <Card className="h-full">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <FileCode className="h-5 w-5" />
                    {currentTemplate?.name}
                  </CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    {currentTemplate?.description}
                  </p>
                </div>
                <Button variant="outline" size="sm" onClick={handleCopy}>
                  {copied ? (
                    <>
                      <Check className="h-4 w-4 mr-2" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4 mr-2" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="bg-muted rounded-lg p-4 overflow-x-auto">
                <pre className="text-sm">
                  <code>{currentTemplate?.code}</code>
                </pre>
              </div>

              <div className="mt-4 p-4 bg-blue-500/10 rounded-lg">
                <div className="flex gap-2">
                  <Sparkles className="h-5 w-5 text-blue-500 flex-shrink-0" />
                  <div className="text-sm">
                    <p className="font-semibold text-blue-500 mb-1">Pro Tip</p>
                    <p className="text-muted-foreground">
                      Replace <code className="bg-muted px-1 rounded">your_api_key</code> with
                      your actual API key from the settings page.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
