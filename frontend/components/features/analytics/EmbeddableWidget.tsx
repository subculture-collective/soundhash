'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Copy, CheckCircle2, Code, Eye, Globe } from 'lucide-react'

interface EmbedConfig {
  widgetType: string
  theme: string
  width: string
  height: string
  refreshInterval: number
}

export function EmbeddableWidget() {
  const [config, setConfig] = useState<EmbedConfig>({
    widgetType: 'api-usage',
    theme: 'light',
    width: '100%',
    height: '400px',
    refreshInterval: 30,
  })
  const [copied, setCopied] = useState(false)
  const [shareToken] = useState('sk_embed_abc123xyz789')

  const generateEmbedCode = () => {
    return `<!-- SoundHash Analytics Widget -->
<div id="soundhash-widget"></div>
<script src="https://analytics.soundhash.com/embed.js"></script>
<script>
  SoundHash.embed({
    token: '${shareToken}',
    type: '${config.widgetType}',
    theme: '${config.theme}',
    width: '${config.width}',
    height: '${config.height}',
    refreshInterval: ${config.refreshInterval},
    target: 'soundhash-widget'
  });
</script>`
  }

  const copyEmbedCode = () => {
    navigator.clipboard.writeText(generateEmbedCode())
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6">
      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Embeddable Analytics Widget</CardTitle>
          <CardDescription>
            Create white-label analytics widgets for your customers
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Widget Type
              </label>
              <select
                value={config.widgetType}
                onChange={(e) =>
                  setConfig({ ...config, widgetType: e.target.value })
                }
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="api-usage">API Usage Chart</option>
                <option value="metrics">Key Metrics</option>
                <option value="matches">Match Statistics</option>
                <option value="activity">User Activity</option>
                <option value="revenue">Revenue Summary</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Theme</label>
              <select
                value={config.theme}
                onChange={(e) => setConfig({ ...config, theme: e.target.value })}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="auto">Auto (System)</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Width</label>
              <Input
                value={config.width}
                onChange={(e) => setConfig({ ...config, width: e.target.value })}
                placeholder="100%"
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Height</label>
              <Input
                value={config.height}
                onChange={(e) =>
                  setConfig({ ...config, height: e.target.value })
                }
                placeholder="400px"
              />
            </div>

            <div className="md:col-span-2">
              <label className="text-sm font-medium mb-2 block">
                Refresh Interval (seconds)
              </label>
              <Input
                type="number"
                value={config.refreshInterval}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    refreshInterval: parseInt(e.target.value),
                  })
                }
                min="10"
                max="300"
              />
              <p className="text-xs text-muted-foreground mt-1">
                How often the widget should refresh data
              </p>
            </div>
          </div>

          <div className="pt-4 border-t">
            <label className="text-sm font-medium mb-2 block">
              Share Token
            </label>
            <div className="flex gap-2">
              <Input value={shareToken} readOnly className="font-mono text-sm" />
              <Button variant="outline" size="sm" className="gap-2">
                <Globe className="h-4 w-4" />
                Generate New
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              This token allows read-only access to the selected widget data
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Preview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Live Preview
          </CardTitle>
          <CardDescription>
            Preview how your widget will appear when embedded
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={`rounded-lg border-2 p-6 ${
              config.theme === 'dark'
                ? 'bg-gray-900 border-gray-700'
                : 'bg-white border-gray-200'
            }`}
            style={{
              width: config.width,
              height: config.height,
            }}
          >
            <div className="h-full flex items-center justify-center">
              <div className="text-center text-muted-foreground">
                <div className="text-4xl mb-2">📊</div>
                <p className="font-medium">
                  {config.widgetType
                    .split('-')
                    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                    .join(' ')}{' '}
                  Widget
                </p>
                <p className="text-sm">Preview will appear here</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Embed Code */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Code className="h-5 w-5" />
            Embed Code
          </CardTitle>
          <CardDescription>
            Copy and paste this code into your website
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="relative">
            <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-xs font-mono">
              <code>{generateEmbedCode()}</code>
            </pre>
            <Button
              size="sm"
              variant="outline"
              className="absolute top-2 right-2 gap-2"
              onClick={copyEmbedCode}
            >
              {copied ? (
                <>
                  <CheckCircle2 className="h-4 w-4" />
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

          {/* Integration Instructions */}
          <div className="rounded-lg border p-4 space-y-2">
            <h4 className="font-semibold text-sm">Integration Steps</h4>
            <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
              <li>Copy the embed code above</li>
              <li>Paste it into your website's HTML</li>
              <li>The widget will automatically load and display your analytics</li>
              <li>
                Customize the appearance using the configuration options above
              </li>
            </ol>
          </div>

          {/* Security Note */}
          <div className="rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-4">
            <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
              <Globe className="h-4 w-4" />
              Security Note
            </h4>
            <p className="text-xs text-muted-foreground">
              The share token provides read-only access to this specific widget.
              You can revoke access at any time by generating a new token. Never
              share your API keys in embedded widgets.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Managed Embeds */}
      <Card>
        <CardHeader>
          <CardTitle>Active Embeds</CardTitle>
          <CardDescription>
            Manage widgets embedded on external sites
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              {
                domain: 'example.com',
                widgetType: 'API Usage',
                views: 1234,
                lastSeen: '2 hours ago',
              },
              {
                domain: 'customer-portal.io',
                widgetType: 'Key Metrics',
                views: 892,
                lastSeen: '5 minutes ago',
              },
              {
                domain: 'dashboard.myapp.com',
                widgetType: 'Match Statistics',
                views: 456,
                lastSeen: '1 day ago',
              },
            ].map((embed, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div>
                  <div className="font-medium">{embed.domain}</div>
                  <div className="text-sm text-muted-foreground">
                    {embed.widgetType} • {embed.views.toLocaleString()} views •
                    Last seen {embed.lastSeen}
                  </div>
                </div>
                <Button size="sm" variant="outline">
                  Revoke
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
