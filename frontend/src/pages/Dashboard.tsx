import { useEffect, useState } from 'react'
import { listJobs, startJob, getSettings, updateSettings, deleteJob } from '../api/client'
import { AutonomousToggle } from '../components/AutonomousToggle'
import { useWebSocket } from '../hooks/useWebSocket'

interface Job {
  job_id: string
  status: string
  created_at: string
  youtube_url?: string
  generation_provider?: string
  generation_model?: string
}

interface Settings {
  autonomous_mode: boolean
  schedule_time: string
  channel_id: string
  default_format: string
  generation_provider: string
  generation_model: string
}

export function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [settings, setSettings] = useState<Settings>({
    autonomous_mode: false,
    schedule_time: '09:00',
    channel_id: '',
    default_format: 'faceless',
    generation_provider: 'gemini',
    generation_model: '',
  })
  const [starting, setStarting] = useState(false)

  const { connected } = useWebSocket((msg: unknown) => {
    const data = msg as { type: string }
    if (data.type === 'stage_update' || data.type === 'log') {
      fetchJobs()
    }
  })

  const fetchJobs = async () => {
    const res = await listJobs()
    setJobs(res.data)
  }

  const fetchSettings = async () => {
    const res = await getSettings()
    setSettings(res.data)
  }

  useEffect(() => {
    fetchJobs()
    fetchSettings()
    const interval = setInterval(fetchJobs, 10000)
    return () => clearInterval(interval)
  }, [])

  const handleToggleAutonomous = async (val: boolean) => {
    await updateSettings({ autonomous_mode: val })
    setSettings((s) => ({ ...s, autonomous_mode: val }))
  }

  const handleStartJob = async () => {
    setStarting(true)
    try {
      await startJob(
        settings.autonomous_mode,
        settings.default_format,
        settings.generation_provider,
        settings.generation_model || undefined,
      )
      await fetchJobs()
    } finally {
      setStarting(false)
    }
  }

  const handleDeleteJob = async (jobId: string) => {
    if (!window.confirm('Delete this pipeline job and its logs?')) return
    await deleteJob(jobId)
    await fetchJobs()
  }

  const totalVideos = jobs.filter((j) => j.youtube_url).length
  const lastUpload = jobs.find((j) => j.youtube_url)

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
        <div className="flex items-center gap-2">
          <span
            className={`h-2 w-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-400'}`}
          />
          <span className="text-xs text-gray-500">{connected ? 'Live' : 'Disconnected'}</span>
        </div>
      </div>

      {/* Autonomous Toggle */}
      <div className="bg-white rounded-2xl shadow p-6">
        <AutonomousToggle enabled={settings.autonomous_mode} onChange={handleToggleAutonomous} />
        <p className="mt-2 text-sm text-gray-500">
          {settings.autonomous_mode
            ? 'The pipeline runs fully automatically on schedule.'
            : 'Manual mode: you approve each stage before it runs.'}
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Stat label="Total Videos Uploaded" value={totalVideos} />
        <Stat
          label="Last Upload"
          value={lastUpload ? new Date(lastUpload.created_at).toLocaleDateString() : '—'}
        />
        <Stat label="Scheduled Time" value={settings.schedule_time} />
      </div>

      {/* Start Job */}
      <div className="bg-white rounded-2xl shadow p-5 grid grid-cols-1 md:grid-cols-3 gap-4">
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-600">Generation Provider</span>
          <select
            value={settings.generation_provider}
            onChange={(e) => setSettings((s) => ({ ...s, generation_provider: e.target.value }))}
            className="input"
          >
            <option value="gemini">Gemini</option>
            <option value="groq">GROQ</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 md:col-span-2">
          <span className="text-sm font-medium text-gray-600">Generation Model</span>
          <input
            value={settings.generation_model}
            onChange={(e) => setSettings((s) => ({ ...s, generation_model: e.target.value }))}
            placeholder={settings.generation_provider === 'groq' ? 'llama-3.3-70b-versatile' : 'gemini-1.5-pro'}
            className="input"
          />
        </label>
      </div>

      <button
        onClick={handleStartJob}
        disabled={starting}
        className="w-full bg-purple-600 text-white py-3 rounded-xl font-semibold text-lg hover:bg-purple-700 transition disabled:opacity-50"
      >
        {starting ? 'Starting...' : '▶ Start New Pipeline Job'}
      </button>

      {/* Recent Jobs */}
      <div className="bg-white rounded-2xl shadow p-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-700">Recent Jobs</h2>
        <div className="space-y-3">
          {jobs.slice(0, 10).map((job) => (
            <div
              key={job.job_id}
              className="flex items-center justify-between border rounded-lg px-4 py-3"
            >
              <span className="font-mono text-sm text-gray-600 truncate w-48">{job.job_id}</span>
              <JobStatusBadge status={job.status} />
              <span className="text-xs text-gray-500">
                {job.generation_provider ?? 'gemini'}
                {job.generation_model ? ` / ${job.generation_model}` : ''}
              </span>
              <span className="text-xs text-gray-400">
                {new Date(job.created_at).toLocaleString()}
              </span>
              {job.youtube_url && (
                <a
                  href={job.youtube_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-blue-600 underline"
                >
                  View
                </a>
              )}
              <button
                onClick={() => handleDeleteJob(job.job_id)}
                className="text-xs text-gray-600 border border-gray-300 px-2 py-1 rounded hover:bg-gray-50"
              >
                Delete
              </button>
            </div>
          ))}
          {jobs.length === 0 && (
            <p className="text-gray-400 text-sm">No jobs yet. Start your first pipeline!</p>
          )}
        </div>
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white rounded-2xl shadow p-5 flex flex-col gap-1">
      <span className="text-2xl font-bold text-gray-800">{value}</span>
      <span className="text-sm text-gray-500">{label}</span>
    </div>
  )
}

function JobStatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    created: 'bg-gray-100 text-gray-600',
    running: 'bg-blue-100 text-blue-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
    cancelled: 'bg-yellow-100 text-yellow-700',
  }
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[status] ?? 'bg-gray-100'}`}>
      {status}
    </span>
  )
}
