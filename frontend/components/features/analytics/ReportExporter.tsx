'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from 'sonner'
import { 
  Download,
  FileText,
  FileSpreadsheet,
  Mail,
  Calendar
} from 'lucide-react'

interface ReportConfig {
  name: string
  type: string
  format: string
  dateRange: string
  includeCharts: boolean
  schedule?: {
    frequency: string
    recipients: string[]
  }
}

export function ReportExporter() {
  const [reportName, setReportName] = useState('')
  const [reportType, setReportType] = useState('usage')
  const [exportFormat, setExportFormat] = useState('pdf')
  const [dateRange, setDateRange] = useState('last-30-days')
  const [includeCharts, setIncludeCharts] = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)
  const [showSchedule, setShowSchedule] = useState(false)
  const [scheduleFrequency, setScheduleFrequency] = useState('weekly')
  const [recipients, setRecipients] = useState('')

  const handleGenerateReport = async () => {
    setIsGenerating(true)
    
    try {
      // Simulate report generation
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // TODO: Implement actual API call
      toast.success('Report generated successfully!', {
        description: `Your ${reportType} report in ${exportFormat.toUpperCase()} format is ready to download`,
      })
    } catch (error) {
      toast.error('Failed to generate report', {
        description: 'Please try again or contact support',
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const handleScheduleReport = async () => {
    try {
      // TODO: Implement API call to schedule report
      const recipientList = recipients.split(',').map(e => e.trim())
      toast.success('Report scheduled successfully!', {
        description: `${scheduleFrequency.charAt(0).toUpperCase() + scheduleFrequency.slice(1)} reports will be sent to ${recipientList.length} recipient(s)`,
      })
    } catch (error) {
      toast.error('Failed to schedule report', {
        description: 'Please check your configuration and try again',
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Report Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Generate Custom Report</CardTitle>
          <CardDescription>
            Create and export custom analytics reports
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Report Details */}
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Report Name
              </label>
              <Input
                value={reportName}
                onChange={(e) => setReportName(e.target.value)}
                placeholder="Enter report name"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Report Type
                </label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="usage">API Usage Report</option>
                  <option value="revenue">Revenue Report</option>
                  <option value="matches">Match Analytics</option>
                  <option value="users">User Activity</option>
                  <option value="custom">Custom Report</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Export Format
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <Button
                    variant={exportFormat === 'pdf' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setExportFormat('pdf')}
                    className="gap-2"
                  >
                    <FileText className="h-4 w-4" />
                    PDF
                  </Button>
                  <Button
                    variant={exportFormat === 'csv' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setExportFormat('csv')}
                    className="gap-2"
                  >
                    <FileSpreadsheet className="h-4 w-4" />
                    CSV
                  </Button>
                  <Button
                    variant={exportFormat === 'excel' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setExportFormat('excel')}
                    className="gap-2"
                  >
                    <FileSpreadsheet className="h-4 w-4" />
                    Excel
                  </Button>
                </div>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Date Range
              </label>
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="last-7-days">Last 7 days</option>
                <option value="last-30-days">Last 30 days</option>
                <option value="last-90-days">Last 90 days</option>
                <option value="last-year">Last year</option>
                <option value="custom">Custom range</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="includeCharts"
                checked={includeCharts}
                onChange={(e) => setIncludeCharts(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="includeCharts" className="text-sm">
                Include charts and visualizations
              </label>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t">
            <Button
              onClick={handleGenerateReport}
              disabled={!reportName || isGenerating}
              className="gap-2"
            >
              {isGenerating ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Generating...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4" />
                  Generate Report
                </>
              )}
            </Button>

            <Button
              variant="outline"
              onClick={() => setShowSchedule(!showSchedule)}
              className="gap-2"
            >
              <Calendar className="h-4 w-4" />
              Schedule Delivery
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Schedule Configuration */}
      {showSchedule && (
        <Card>
          <CardHeader>
            <CardTitle>Schedule Report Delivery</CardTitle>
            <CardDescription>
              Automatically generate and email reports on a schedule
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Frequency
              </label>
              <select
                value={scheduleFrequency}
                onChange={(e) => setScheduleFrequency(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly (Monday morning)</option>
                <option value="monthly">Monthly (1st of month)</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Email Recipients
              </label>
              <Input
                value={recipients}
                onChange={(e) => setRecipients(e.target.value)}
                placeholder="email1@example.com, email2@example.com"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Separate multiple emails with commas
              </p>
            </div>

            <Button
              onClick={handleScheduleReport}
              disabled={!reportName || !recipients}
              className="gap-2"
            >
              <Mail className="h-4 w-4" />
              Schedule Report
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Scheduled Reports */}
      <Card>
        <CardHeader>
          <CardTitle>Scheduled Reports</CardTitle>
          <CardDescription>
            Manage your scheduled report deliveries
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              {
                name: 'Weekly Usage Report',
                frequency: 'Weekly',
                format: 'PDF',
                recipients: 2,
                nextRun: '2024-11-04',
              },
              {
                name: 'Monthly Revenue Analysis',
                frequency: 'Monthly',
                format: 'Excel',
                recipients: 3,
                nextRun: '2024-12-01',
              },
            ].map((report, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex-1">
                  <div className="font-medium">{report.name}</div>
                  <div className="text-sm text-muted-foreground">
                    {report.frequency} • {report.format} • {report.recipients}{' '}
                    recipients
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Next run: {report.nextRun}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline">
                    Edit
                  </Button>
                  <Button size="sm" variant="outline">
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Reports */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Reports</CardTitle>
          <CardDescription>
            Download previously generated reports
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              {
                name: 'API Usage Report',
                date: '2024-10-30',
                format: 'PDF',
                size: '2.4 MB',
              },
              {
                name: 'Revenue Analysis Q3',
                date: '2024-10-28',
                format: 'Excel',
                size: '1.8 MB',
              },
              {
                name: 'Match Analytics',
                date: '2024-10-25',
                format: 'CSV',
                size: '890 KB',
              },
            ].map((report, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded">
                    {report.format === 'PDF' ? (
                      <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    ) : (
                      <FileSpreadsheet className="h-5 w-5 text-green-600 dark:text-green-400" />
                    )}
                  </div>
                  <div>
                    <div className="font-medium">{report.name}</div>
                    <div className="text-sm text-muted-foreground">
                      {report.date} • {report.size}
                    </div>
                  </div>
                </div>
                <Button size="sm" variant="outline" className="gap-2">
                  <Download className="h-4 w-4" />
                  Download
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
