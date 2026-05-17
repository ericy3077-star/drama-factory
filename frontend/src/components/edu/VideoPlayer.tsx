'use client'

import { useRef, useState, useEffect } from 'react'
import { Play, Pause, Volume2, VolumeX, Maximize, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn, formatDuration } from '@/lib/utils'

interface VideoPlayerProps {
  src: string
  poster?: string
  title?: string
  className?: string
}

export function VideoPlayer({ src, poster, title, className }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [progress, setProgress] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [showControls, setShowControls] = useState(true)
  const hideControlsTimer = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const onTimeUpdate = () => setProgress(video.currentTime / (video.duration || 1) * 100)
    const onLoadedMetadata = () => { setDuration(video.duration); setIsLoading(false) }
    const onEnded = () => setIsPlaying(false)
    const onWaiting = () => setIsLoading(true)
    const onCanPlay = () => setIsLoading(false)

    video.addEventListener('timeupdate', onTimeUpdate)
    video.addEventListener('loadedmetadata', onLoadedMetadata)
    video.addEventListener('ended', onEnded)
    video.addEventListener('waiting', onWaiting)
    video.addEventListener('canplay', onCanPlay)

    return () => {
      video.removeEventListener('timeupdate', onTimeUpdate)
      video.removeEventListener('loadedmetadata', onLoadedMetadata)
      video.removeEventListener('ended', onEnded)
      video.removeEventListener('waiting', onWaiting)
      video.removeEventListener('canplay', onCanPlay)
    }
  }, [])

  function togglePlay() {
    const video = videoRef.current
    if (!video) return
    if (isPlaying) { video.pause(); setIsPlaying(false) }
    else { video.play(); setIsPlaying(true) }
  }

  function toggleMute() {
    const video = videoRef.current
    if (!video) return
    video.muted = !isMuted
    setIsMuted(!isMuted)
  }

  function seek(e: React.MouseEvent<HTMLDivElement>) {
    const video = videoRef.current
    if (!video) return
    const rect = e.currentTarget.getBoundingClientRect()
    const ratio = (e.clientX - rect.left) / rect.width
    video.currentTime = ratio * video.duration
  }

  function fullscreen() {
    videoRef.current?.requestFullscreen()
  }

  function handleMouseMove() {
    setShowControls(true)
    clearTimeout(hideControlsTimer.current)
    hideControlsTimer.current = setTimeout(() => setShowControls(false), 3000)
  }

  const currentTime = videoRef.current ? videoRef.current.currentTime : 0

  return (
    <div
      className={cn('relative bg-black rounded-xl overflow-hidden group', className)}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => isPlaying && setShowControls(false)}
    >
      <video
        ref={videoRef}
        src={src}
        poster={poster}
        className="w-full aspect-video"
        onClick={togglePlay}
      />

      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/40">
          <Loader2 className="h-10 w-10 text-white animate-spin" />
        </div>
      )}

      {/* Controls */}
      <div
        className={cn(
          'absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-4 transition-opacity duration-300',
          showControls || !isPlaying ? 'opacity-100' : 'opacity-0',
        )}
      >
        {title && <p className="text-white text-sm font-medium mb-2 truncate">{title}</p>}

        {/* Progress bar */}
        <div
          className="h-1.5 bg-white/30 rounded-full cursor-pointer mb-3 hover:h-2.5 transition-all"
          onClick={seek}
        >
          <div
            className="h-full bg-white rounded-full relative"
            style={{ width: `${progress}%` }}
          >
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow" />
          </div>
        </div>

        {/* Buttons row */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="h-8 w-8 text-white hover:bg-white/20" onClick={togglePlay}>
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-white hover:bg-white/20" onClick={toggleMute}>
            {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
          </Button>
          <span className="text-white text-xs ml-1">
            {formatDuration(currentTime)} / {formatDuration(duration)}
          </span>
          <div className="flex-1" />
          <Button variant="ghost" size="icon" className="h-8 w-8 text-white hover:bg-white/20" onClick={fullscreen}>
            <Maximize className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
