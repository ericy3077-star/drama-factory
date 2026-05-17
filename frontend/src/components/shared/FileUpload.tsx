'use client'

import { useCallback, useState } from 'react'
import { useDropzone, type Accept } from 'react-dropzone'
import { Upload, File, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { cn, formatBytes } from '@/lib/utils'
import { tokenStorage } from '@/lib/api'
import { toast } from 'sonner'

interface UploadedFile {
  file: File
  id: string
  status: 'uploading' | 'done' | 'error'
  progress: number
  assetId?: string
  error?: string
}

interface FileUploadProps {
  accept?: Accept
  maxSize?: number
  maxFiles?: number
  uploadUrl: string
  onUploadComplete?: (assetId: string, file: File) => void
  className?: string
}

export function FileUpload({
  accept,
  maxSize = 50 * 1024 * 1024,
  maxFiles = 10,
  uploadUrl,
  onUploadComplete,
  className,
}: FileUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([])

  async function uploadFile(item: UploadedFile) {
    const formData = new FormData()
    formData.append('file', item.file)

    const token = tokenStorage.getAccess()

    return new Promise<void>((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('POST', `${process.env.NEXT_PUBLIC_API_URL}${uploadUrl}`)
      if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 100)
          setFiles((prev) =>
            prev.map((f) => (f.id === item.id ? { ...f, progress: pct } : f)),
          )
        }
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const res = JSON.parse(xhr.responseText)
            const assetId = res?.data?.id ?? res?.id
            setFiles((prev) =>
              prev.map((f) => (f.id === item.id ? { ...f, status: 'done', assetId, progress: 100 } : f)),
            )
            onUploadComplete?.(assetId, item.file)
            resolve()
          } catch {
            reject(new Error('Invalid response'))
          }
        } else {
          reject(new Error(`Upload failed: ${xhr.status}`))
        }
      }

      xhr.onerror = () => reject(new Error('Network error'))
      xhr.send(formData)
    })
  }

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const newItems: UploadedFile[] = acceptedFiles.map((f) => ({
        file: f,
        id: Math.random().toString(36).slice(2),
        status: 'uploading',
        progress: 0,
      }))

      setFiles((prev) => [...prev, ...newItems])

      await Promise.allSettled(
        newItems.map((item) =>
          uploadFile(item).catch((err) => {
            const msg = err instanceof Error ? err.message : '上传失败'
            setFiles((prev) =>
              prev.map((f) => (f.id === item.id ? { ...f, status: 'error', error: msg } : f)),
            )
            toast.error(`${item.file.name} 上传失败`)
          }),
        ),
      )
    },
    [uploadUrl, onUploadComplete],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxSize,
    maxFiles,
    onDropRejected: (rejected) => {
      rejected.forEach((r) => {
        r.errors.forEach((e) => toast.error(e.message))
      })
    },
  })

  function removeFile(id: string) {
    setFiles((prev) => prev.filter((f) => f.id !== id))
  }

  return (
    <div className={cn('space-y-4', className)}>
      <div
        {...getRootProps()}
        className={cn(
          'rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-colors',
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/50 hover:bg-accent/30',
        )}
      >
        <input {...getInputProps()} />
        <Upload className={cn('h-10 w-10 mx-auto mb-3', isDragActive ? 'text-primary' : 'text-muted-foreground')} />
        <p className="text-sm font-medium">
          {isDragActive ? '释放以上传' : '拖放文件到此处，或点击选择'}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          最大 {formatBytes(maxSize)}，最多 {maxFiles} 个文件
        </p>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((item) => (
            <div key={item.id} className="flex items-center gap-3 rounded-lg border p-3">
              <File className="h-5 w-5 shrink-0 text-muted-foreground" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{item.file.name}</p>
                <p className="text-xs text-muted-foreground">{formatBytes(item.file.size)}</p>
                {item.status === 'uploading' && (
                  <Progress value={item.progress} className="h-1 mt-1.5" />
                )}
                {item.status === 'error' && (
                  <p className="text-xs text-destructive mt-1">{item.error}</p>
                )}
              </div>
              <div className="shrink-0">
                {item.status === 'uploading' && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
                {item.status === 'done' && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                {item.status === 'error' && <AlertCircle className="h-4 w-4 text-destructive" />}
              </div>
              <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={() => removeFile(item.id)}>
                <X className="h-3.5 w-3.5" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
