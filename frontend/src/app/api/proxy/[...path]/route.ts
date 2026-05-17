import { type NextRequest, NextResponse } from 'next/server'
import { tokenStorage } from '@/lib/api'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function proxyRequest(req: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path.join('/')
  const url = new URL(req.url)
  const target = `${API_URL}/api/v1/${path}${url.search}`

  const headers: HeadersInit = {
    'Content-Type': req.headers.get('Content-Type') ?? 'application/json',
  }

  const token = req.headers.get('Authorization') ?? `Bearer ${tokenStorage.getAccess()}`
  if (token) headers['Authorization'] = token

  const body = req.method !== 'GET' && req.method !== 'HEAD' ? await req.text() : undefined

  const response = await fetch(target, {
    method: req.method,
    headers,
    body,
  })

  const data = await response.text()
  return new NextResponse(data, {
    status: response.status,
    headers: {
      'Content-Type': response.headers.get('Content-Type') ?? 'application/json',
    },
  })
}

export const GET = proxyRequest
export const POST = proxyRequest
export const PUT = proxyRequest
export const DELETE = proxyRequest
export const PATCH = proxyRequest
