import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { FeedItem, ChatSession, FeedCategory } from '@/types/invest'

interface InvestState {
  // Feed
  feedFilter: FeedCategory | 'all'
  setFeedFilter: (f: FeedCategory | 'all') => void

  // Active chat session
  activeChatSessionId: string | null
  setActiveChatSession: (id: string | null) => void

  // Local session cache (before persistence to server)
  localSessions: Record<string, ChatSession>
  upsertSession: (session: ChatSession) => void

  // Selected tickers (watchlist quick filter)
  watchlistTickers: string[]
  addTicker: (ticker: string) => void
  removeTicker: (ticker: string) => void
}

export const useInvestStore = create<InvestState>()(
  persist(
    (set) => ({
      feedFilter: 'all',
      setFeedFilter: (feedFilter) => set({ feedFilter }),

      activeChatSessionId: null,
      setActiveChatSession: (activeChatSessionId) => set({ activeChatSessionId }),

      localSessions: {},
      upsertSession: (session) =>
        set((state) => ({
          localSessions: { ...state.localSessions, [session.id]: session },
        })),

      watchlistTickers: [],
      addTicker: (ticker) =>
        set((state) => ({
          watchlistTickers: state.watchlistTickers.includes(ticker)
            ? state.watchlistTickers
            : [...state.watchlistTickers, ticker],
        })),
      removeTicker: (ticker) =>
        set((state) => ({
          watchlistTickers: state.watchlistTickers.filter((t) => t !== ticker),
        })),
    }),
    {
      name: 'df-invest',
      partialize: (state) => ({
        feedFilter: state.feedFilter,
        watchlistTickers: state.watchlistTickers,
      }),
    },
  ),
)
