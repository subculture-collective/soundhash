'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, Loader2, CheckCircle, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'
import { toast } from 'sonner'
import api from '@/lib/api'

interface AudioUploaderProps {
  onUploadComplete?: (data: any) => void
}

export function AudioUploader({ onUploadComplete }: AudioUploaderProps) {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return
    
    setUploadedFile(file)
    setUploading(true)
    setProgress(0)
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await api.post('/videos/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
            setProgress(percent)
          }
        }
      })
      
      toast.success('File uploaded successfully!')
      onUploadComplete?.(response.data)
    } catch (error: any) {
      console.error('Upload error:', error)
      toast.error(error.response?.data?.message || 'Upload failed. Please try again.')
      setUploadedFile(null)
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }, [onUploadComplete])
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.ogg', '.flac'],
      'video/*': ['.mp4', '.webm', '.mov', '.avi']
    },
    maxSize: 100 * 1024 * 1024, // 100MB
    multiple: false,
    disabled: uploading,
  })

  const clearFile = () => {
    setUploadedFile(null)
    setProgress(0)
  }
  
  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={cn(
          "relative border-2 border-dashed rounded-lg p-12 transition-all duration-200 cursor-pointer",
          isDragActive 
            ? "border-primary bg-primary/5" 
            : "border-border hover:border-primary/50",
          uploading && "pointer-events-none opacity-50"
        )}
      >
        <input {...getInputProps()} />
        
        <AnimatePresence mode="wait">
          {uploading ? (
            <motion.div
              key="uploading"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="text-center"
            >
              <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-primary" />
              <p className="text-lg font-medium mb-2">Uploading... {progress}%</p>
              <div className="w-full max-w-xs mx-auto bg-secondary rounded-full h-2 overflow-hidden">
                <motion.div
                  className="h-full bg-primary"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            </motion.div>
          ) : uploadedFile ? (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="text-center"
            >
              <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
              <p className="text-lg font-medium mb-2">Upload Complete!</p>
              <p className="text-sm text-muted-foreground mb-4">{uploadedFile.name}</p>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  clearFile()
                }}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-destructive hover:text-destructive/80 transition-colors"
              >
                <X className="w-4 h-4" />
                Clear
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="idle"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="text-center"
            >
              <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-lg font-medium mb-2">
                {isDragActive ? 'Drop your file here' : 'Drop audio or video file here'}
              </p>
              <p className="text-sm text-muted-foreground mb-4">
                or click to browse
              </p>
              <p className="text-xs text-muted-foreground">
                Supports: MP3, WAV, M4A, OGG, FLAC, MP4, WebM, MOV, AVI (Max 100MB)
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
