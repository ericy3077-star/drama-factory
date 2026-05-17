'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiDelete } from '@/lib/api'
import type { MemoryFragment } from '@/types/invest'
import { toast } from 'sonner'

export function useMemory(vertical: 'invest' | 'edu') {
  const queryClient = useQueryClient()
  const key = ['memories', vertical]

  const { data: memories = [], isLoading, refetch } = useQuery({
    queryKey: key,
    queryFn: () => apiGet<MemoryFragment[]>(`/api/v1/${vertical}/memory`),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiDelete(`/api/v1/${vertical}/memory/${id}`),
    onSuccess: (_, id) => {
      queryClient.setQueryData<MemoryFragment[]>(key, (prev) =>
        prev ? prev.filter((m) => m.id !== id) : [],
      )
      toast.success('记忆已删除')
    },
    onError: () => toast.error('删除失败'),
  })

  return {
    memories,
    isLoading,
    refetch,
    deleteMemory: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending,
  }
}
