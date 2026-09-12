interface AuthTokens {
  accessToken: string
  refreshToken: string
}

const TOKEN_KEY = 'consight_tokens'

export function getAuthTokens(): AuthTokens | null {
  try {
    const stored = localStorage.getItem(TOKEN_KEY)
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

export function setAuthTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(TOKEN_KEY, JSON.stringify({ accessToken, refreshToken }))
}

export function clearAuthTokens(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export function isAuthenticated(): boolean {
  return !!getAuthTokens()
}

export function getAccessToken(): string | null {
  return getAuthTokens()?.accessToken ?? null
}

export function getRefreshToken(): string | null {
  return getAuthTokens()?.refreshToken ?? null
}