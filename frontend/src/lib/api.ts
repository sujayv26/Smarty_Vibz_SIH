import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { getAuthTokens, setAuthTokens, clearAuthTokens } from './auth'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// Request interceptor to add CSRF token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const csrfToken = document.cookie
      .split('; ')
      .find((row) => row.startsWith('csrf_token='))
      ?.split('=')[1]

    if (csrfToken && config.method !== 'get') {
      config.headers['X-CSRF-Token'] = csrfToken
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for token refresh
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value: unknown) => void
  reject: (reason: unknown) => void
}> = []

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(() => api(originalRequest))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshToken = getAuthTokens()?.refreshToken
        if (!refreshToken) throw new Error('No refresh token')

        const response = await axios.post(
          `${API_BASE_URL}/auth/refresh`,
          { refresh_token: refreshToken },
          { withCredentials: true }
        )

        const { access_token, refresh_token } = response.data
        setAuthTokens(access_token, refresh_token)

        processQueue(null, access_token)
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        clearAuthTokens()
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
  getUsers: () => api.get('/auth/users'),
  createUser: (data: unknown) => api.post('/auth/users', data),
  getCsrfToken: () => api.post('/auth/csrf-token'),
}

export const scheduleApi = {
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/schedule/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  getActivities: (params?: { project_id?: number }) =>
    api.get('/schedule/activities', { params }),
  getActivity: (id: number) => api.get(`/schedule/activities/${id}`),
  importXer: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/schedule/import/xer', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  exportXer: (projectId: number) =>
    api.get(`/schedule/export/xer/${projectId}`, { responseType: 'blob' }),
}

export const progressApi = {
  extract: (rawText: string) => api.post('/progress/extract', { raw_text: rawText }),
  uploadExcel: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/progress/upload-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  getEvents: (params?: { project_id?: number; limit?: number }) =>
    api.get('/progress/events', { params }),
  getEvent: (id: number) => api.get(`/progress/events/${id}`),
}

export const matchingApi = {
  run: (eventId: number) => api.post(`/matching/run/${eventId}`),
  getResult: (eventId: number) => api.get(`/matching/result/${eventId}`),
  getQueue: (params?: { project_id?: number; status?: string }) =>
    api.get('/matching/queue', { params }),
}

export const confidenceApi = {
  evaluate: (eventId: number) => api.post(`/confidence/evaluate/${eventId}`),
  getResult: (eventId: number) => api.get(`/confidence/result/${eventId}`),
}

export const reviewsApi = {
  getPending: (params?: { project_id?: number }) => api.get('/reviews/pending', { params }),
  getById: (id: number) => api.get(`/reviews/${id}`),
  approve: (id: number, note?: string) => api.post(`/reviews/${id}/approve`, { reviewer_note: note }),
  correct: (id: number, activityId: number, note?: string) =>
    api.post(`/reviews/${id}/correct`, { final_activity_id: activityId, reviewer_note: note }),
  reject: (id: number, note?: string) => api.post(`/reviews/${id}/reject`, { reviewer_note: note }),
  createNewActivity: (id: number, data: unknown) => api.post(`/reviews/${id}/new-activity`, data),
}

export const analyticsApi = {
  getDisciplineSummary: (projectId: number) =>
    api.get(`/analytics/discipline-summary/${projectId}`),
  getBenchmarks: (projectId: number) =>
    api.get(`/knowledge-base/benchmarks/${projectId}`),
  getDelayPredictions: (projectId: number) =>
    api.get(`/analytics/delay-predictions/${projectId}`),
}

export const agentApi = {
  chat: (message: string, sessionId: string) =>
    api.post('/agent/chat', { message, session_id: sessionId }),
  getSessionEvents: (sessionId: string) => api.get(`/agent/sessions/${sessionId}/events`),
}

export const auditApi = {
  getLogs: (params?: { project_id?: number; limit?: number }) =>
    api.get('/audit/logs', { params }),
}

export const wbsApi = {
  getTree: (projectId: number) => api.get(`/wbs/tree/${projectId}`),
  getNode: (id: number) => api.get(`/wbs/nodes/${id}`),
  updateActuals: (id: number, data: { actual_start?: string; actual_finish?: string }) =>
    api.patch(`/wbs/nodes/${id}`, data),
}