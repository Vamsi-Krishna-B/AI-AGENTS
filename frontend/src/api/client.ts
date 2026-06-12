import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Jobs
export const startJob = (
  autonomous: boolean,
  format_type: string,
  generation_provider: string,
  generation_model?: string,
) =>
  api.post('/api/jobs/start', {
    autonomous,
    format_type,
    generation_provider,
    generation_model,
  })

export const listJobs = () => api.get('/api/jobs')

export const getJob = (jobId: string) => api.get(`/api/jobs/${jobId}`)

export const approveStage = (jobId: string, stage: string) =>
  api.put(`/api/jobs/${jobId}/approve/${stage}`)

export const cancelJob = (jobId: string) => api.put(`/api/jobs/${jobId}/cancel`)

export const retryJob = (jobId: string) => api.post(`/api/jobs/${jobId}/retry`)

export const deleteJob = (jobId: string) => api.delete(`/api/jobs/${jobId}`)

// Settings
export const getSettings = () => api.get('/api/settings')
export const updateSettings = (data: Record<string, unknown>) => api.put('/api/settings', data)

// Analytics
export const getAnalytics = (refresh = false) =>
  api.get(`/api/analytics?refresh=${refresh}`)
