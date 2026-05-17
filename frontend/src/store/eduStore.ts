import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { DigitalAvatar, VideoJob } from '@/types/edu'

interface EduState {
  // Selected avatar in studio
  selectedAvatarId: string | null
  setSelectedAvatar: (id: string | null) => void

  // Active video jobs (for progress display)
  activeVideoJobs: VideoJob[]
  upsertVideoJob: (job: VideoJob) => void
  removeVideoJob: (id: string) => void

  // Script drafts per avatar
  scriptDrafts: Record<string, string>
  setScriptDraft: (avatarId: string, script: string) => void
  getScriptDraft: (avatarId: string) => string
}

export const useEduStore = create<EduState>()(
  persist(
    (set, get) => ({
      selectedAvatarId: null,
      setSelectedAvatar: (selectedAvatarId) => set({ selectedAvatarId }),

      activeVideoJobs: [],
      upsertVideoJob: (job) =>
        set((state) => {
          const idx = state.activeVideoJobs.findIndex((j) => j.id === job.id)
          const updated =
            idx >= 0
              ? state.activeVideoJobs.map((j, i) => (i === idx ? job : j))
              : [...state.activeVideoJobs, job]
          return { activeVideoJobs: updated }
        }),
      removeVideoJob: (id) =>
        set((state) => ({
          activeVideoJobs: state.activeVideoJobs.filter((j) => j.id !== id),
        })),

      scriptDrafts: {},
      setScriptDraft: (avatarId, script) =>
        set((state) => ({
          scriptDrafts: { ...state.scriptDrafts, [avatarId]: script },
        })),
      getScriptDraft: (avatarId) => get().scriptDrafts[avatarId] ?? '',
    }),
    {
      name: 'df-edu',
      partialize: (state) => ({
        selectedAvatarId: state.selectedAvatarId,
        scriptDrafts: state.scriptDrafts,
      }),
    },
  ),
)
