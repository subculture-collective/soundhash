'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { RefreshCw, X, Play } from 'lucide-react'
import api from '@/lib/api'
import { formatRelativeTime } from '@/lib/utils'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

interface Job {
  id: number
  job_type: string
  status: string
  target_id: string
  progress: number
  current_step?: string
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
}

export default function JobsPage() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  const { data, refetch, isLoading } = useQuery({
    queryKey: ['admin-jobs', statusFilter],
    queryFn: async () => {
      const response = await api.get('/admin/jobs', {
        params: { status_filter: statusFilter, per_page: 100 },
      })
      return response.data
    },
    refetchInterval: 5000, // Auto-refresh every 5s
  })

  const retryJob = useMutation({
    mutationFn: async (jobId: number) => {
      await api.post(`/admin/jobs/${jobId}/retry`)
    },
    onSuccess: () => {
      refetch()
      toast.success('Job restarted')
    },
    onError: () => {
      toast.error('Failed to restart job')
    },
  })

  const cancelJob = useMutation({
    mutationFn: async (jobId: number) => {
      await api.post(`/admin/jobs/${jobId}/cancel`)
    },
    onSuccess: () => {
      refetch()
      toast.success('Job cancelled')
    },
    onError: () => {
      toast.error('Failed to cancel job')
    },
  })

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-500',
      running: 'bg-blue-500',
      completed: 'bg-green-500',
      failed: 'bg-red-500',
      cancelled: 'bg-gray-500',
    }
    return colors[status] || 'bg-gray-500'
  }

  const jobs: Job[] = data?.data || []

  // Calculate stats
  const stats = {
    pending: jobs.filter((j) => j.status === 'pending').length,
    running: jobs.filter((j) => j.status === 'running').length,
    completed: jobs.filter((j) => j.status === 'completed').length,
    failed: jobs.filter((j) => j.status === 'failed').length,
    cancelled: jobs.filter((j) => j.status === 'cancelled').length,
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Processing Jobs</h1>
        <Button onClick={() => refetch()} variant="outline">
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Job Statistics */}
      <div className="grid grid-cols-5 gap-4">
        {['pending', 'running', 'completed', 'failed', 'cancelled'].map((status) => (
          <Card
            key={status}
            className={cn(
              'cursor-pointer transition-colors',
              statusFilter === status && 'ring-2 ring-primary'
            )}
            onClick={() => setStatusFilter(statusFilter === status ? null : status)}
          >
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium capitalize">
                {status}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">
                {stats[status as keyof typeof stats] || 0}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Jobs Table */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Job ID</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Progress</TableHead>
              <TableHead>Current Step</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : jobs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center">
                  No jobs found
                </TableCell>
              </TableRow>
            ) : (
              jobs.map((job) => (
                <TableRow key={job.id}>
                  <TableCell className="font-mono text-sm">{job.id}</TableCell>
                  <TableCell className="capitalize">{job.job_type.replace('_', ' ')}</TableCell>
                  <TableCell>
                    <Badge className={cn('text-white', getStatusColor(job.status))}>
                      {job.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-24 rounded-full bg-gray-200">
                        <div
                          className="h-2 rounded-full bg-blue-600"
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>
                      <span className="text-sm">{Math.round(job.progress)}%</span>
                    </div>
                  </TableCell>
                  <TableCell className="max-w-xs truncate">
                    {job.current_step || '-'}
                  </TableCell>
                  <TableCell>{formatRelativeTime(job.created_at)}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      {job.status === 'failed' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => retryJob.mutate(job.id)}
                        >
                          <Play className="h-3 w-3" />
                        </Button>
                      )}
                      {['pending', 'running'].includes(job.status) && (
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => {
                            if (confirm('Are you sure you want to cancel this job?')) {
                              cancelJob.mutate(job.id)
                            }
                          }}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
