import type { NextAuthOptions } from 'next-auth'
import CredentialsProvider from 'next-auth/providers/credentials'
import { apiPost } from './api'
import { tokenStorage } from './api'
import type { AuthTokens, User } from '@/types/api'

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null

        try {
          const result = await apiPost<{ tokens: AuthTokens; user: User }>(
            '/api/v1/auth/login',
            {
              email: credentials.email,
              password: credentials.password,
            },
          )

          tokenStorage.set(result.tokens)

          return {
            id: result.user.id,
            email: result.user.email,
            name: result.user.name,
            image: result.user.avatar_url,
            accessToken: result.tokens.access_token,
            refreshToken: result.tokens.refresh_token,
          }
        } catch {
          return null
        }
      },
    }),
  ],
  pages: {
    signIn: '/login',
    error: '/login',
  },
  session: {
    strategy: 'jwt',
    maxAge: 7 * 24 * 60 * 60, // 7 days
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = (user as Record<string, unknown>).accessToken
        token.refreshToken = (user as Record<string, unknown>).refreshToken
      }
      return token
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string
      return session
    },
  },
}

// Extend next-auth types
declare module 'next-auth' {
  interface Session {
    accessToken?: string
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    accessToken?: string
    refreshToken?: string
  }
}
