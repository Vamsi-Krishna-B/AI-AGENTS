import { useEffect, useState } from 'react'
import { listJobs, getJob } from '../api/client'

interface Job {
  job_id: string
  status: string
  stages: {
    research?: { output?: { title?: string } }
    thumbnail?: { output?: { thumbnail_path?: string } }
  }
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function Thumbnail() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [job, setJob] = useState<Job | null>(null)

  useEffect(() => {
    listJobs().then((r) => setJobs(r.data))
  }, [])

  useEffect(() => {
    if (!selectedId) return
    getJob(selectedId).then((r) => setJob(r.data))
  }, [selectedId])

  const thumbnailPath = job?.stages?.thumbnail?.output?.thumbnail_path
  const title = job?.stages?.research?.output?.title ?? ''

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-800">Thumbnail Preview</h1>
        <select
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm text-gray-700"
        >
          <option value="">— Select Job —</option>
          {jobs
            .filter((j) => j.stages?.thumbnail?.output)
            .map((j) => (
              <option key={j.job_id} value={j.job_id}>
                {j.job_id.slice(0, 8)} ({j.status})
              </option>
            ))}
        </select>
      </div>

      {!thumbnailPath ? (
        <p className="text-gray-400">Select a job with a completed thumbnail stage.</p>
      ) : (
        <div className="bg-white rounded-2xl shadow p-6 space-y-4 max-w-2xl">
          <h2 className="text-lg font-semibold text-gray-700">{title}</h2>
          <img
            src={`${API_BASE}/storage/thumbnails/${thumbnailPath.split('/').pop()}`}
            alt="Thumbnail"
            className="w-full rounded-xl border shadow"
          />
          <div className="text-xs text-gray-400 break-all">{thumbnailPath}</div>
        </div>
      )}
    </div>
  )
}
