'use client'

import { useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface StreamingTextProps {
  text: string
  isStreaming?: boolean
  markdown?: boolean
  className?: string
  speed?: number // chars per tick
}

export function StreamingText({ text, isStreaming = false, markdown = false, className, speed = 3 }: StreamingTextProps) {
  const [displayed, setDisplayed] = useState('')
  const indexRef = useRef(0)
  const prevTextRef = useRef('')

  useEffect(() => {
    // If text grew (streaming), animate the new part
    if (text.startsWith(prevTextRef.current)) {
      prevTextRef.current = text
      // Already showing all text → jump to end
      if (indexRef.current >= text.length) {
        setDisplayed(text)
        return
      }
      const interval = setInterval(() => {
        indexRef.current = Math.min(indexRef.current + speed, text.length)
        setDisplayed(text.slice(0, indexRef.current))
        if (indexRef.current >= text.length) clearInterval(interval)
      }, 16)
      return () => clearInterval(interval)
    } else {
      // Text was reset — show immediately
      setDisplayed(text)
      indexRef.current = text.length
      prevTextRef.current = text
    }
  }, [text, speed])

  const content = isStreaming ? displayed : text

  return (
    <div className={cn('', className)}>
      {markdown ? (
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>
      ) : (
        <span className="whitespace-pre-wrap">{content}</span>
      )}
      {isStreaming && content.length < text.length && (
        <span className="inline-block w-0.5 h-4 bg-current ml-0.5 align-text-bottom animate-cursor-blink" />
      )}
    </div>
  )
}
