import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { listJobs, getJob, cancelJob, retryJob, deleteJob } from '../api/client'
import { AgentStatusCard } from '../components/AgentStatusCard'
import { LiveLogStream } from '../components/LiveLogStream'
import { StageApproval } from '../components/StageApproval'
import { useWebSocket } from '../hooks/useWebSocket'

const STAGES = ['research', 'script', 'media', 'voice', 'editor', 'thumbnail', 'upload']

interface StageData {
  status: string
  output: unknown
  updated_at: string | null
}

interface Job {
  job_id: string
  status: string
  created_at: string
  autonomous: boolean
  format_type: string
  generation_provider?: string
  generation_model?: string
  retry_of?: string
  stages: Record<string, StageData>
  youtube_url?: string
  logs?: Array<{ agent: string; level: string; message: string; timestamp: string }>
}

export function PipelineMonitor() {
  const { jobId: paramJobId } = useParams<{ jobId?: string }>()
  const [jobs, setJobs] = useState<Job[]>([])
  const [selectedId, setSelectedId] = useState<string>(paramJobId ?? '')
  const [job, setJob] = useState<Job | null>(null)

  useWebSocket((msg: unknown) => {
    const data = msg as { type: string; job_id: string }
    if (
      (data.type === 'stage_update' || data.type === 'log') &&
      data.job_id === selectedId
    ) {
      fetchJob(data.job_id)
    }
  })

  const fetchJobs = async () => {
    const res = await listJobs()
    setJobs(res.data)
  }

  const fetchJob = async (id: string) => {
    const res = await getJob(id)
    setJob(res.data)
  }

  useEffect(() => {
    fetchJobs()
  }, [])

  useEffect(() => {
    if (!selectedId && jobs.length > 0) {
      setSelectedId(jobs[0].job_id)
    }
  }, [jobs])

  useEffect(() => {
    if (selectedId) fetchJob(selectedId)
    const interval = setInterval(() => {
      if (selectedId) fetchJob(selectedId)
    }, 5000)
    return () => clearInterval(interval)
  }, [selectedId])

  const handleCancel = async () => {
    if (!selectedId) return
    await cancelJob(selectedId)
    fetchJob(selectedId)
  }

  const handleRetry = async () => {
    if (!selectedId) return
    const res = await retryJob(selectedId)
    const retryId = res.data.job_id
    await fetchJobs()
    setSelectedId(retryId)
  }

  const handleDelete = async () => {
    if (!selectedId || !window.confirm('Delete this pipeline job and its logs?')) return
    await deleteJob(selectedId)
    setJob(null)
    setSelectedId('')
    await fetchJobs()
  }

  return (
    <div className="p-6 flex gap-6 h-full">
      {/* Job list sidebar */}
      <div className="w-64 flex-shrink-0 bg-white rounded-2xl shadow p-4 space-y-2 overflow-y-auto">
        <h2 className="font-semibold text-gray-700 mb-2">Jobs</h2>
        {jobs.map((j) => (
          <button
            key={j.job_id}
            onClick={() => setSelectedId(j.job_id)}
            className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
              j.job_id === selectedId
                ? 'bg-purple-100 text-purple-800 font-semibold'
                : 'hover:bg-gray-100 text-gray-600'
            }`}
          >
            <div className="truncate">{j.job_id.slice(0, 8)}...</div>
            <div className="text-xs text-gray-400">{j.status}</div>
          </button>
        ))}
      </div>

      {/* Job detail */}
      <div className="flex-1 space-y-4 overflow-y-auto">
        {!job ? (
          <div className="text-gray-400 mt-10 text-center">Select a job to monitor</div>
        ) : (
          <>
            <div className="bg-white rounded-2xl shadow p-5 flex items-center justify-between">
              <div>
                <div className="font-mono text-sm text-gray-500">{job.job_id}</div>
                <div className="flex gap-2 mt-1">
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                    {job.format_type}
                  </span>
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                    {job.autonomous ? 'autonomous' : 'manual'}
                  </span>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-purple-100 text-purple-700">
                    {job.status}
                  </span>
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                    {job.generation_provider ?? 'gemini'}
                    {job.generation_model ? ` / ${job.generation_model}` : ''}
                  </span>
                  {job.retry_of && (
                    <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded">
                      retry
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {['failed', 'cancelled'].includes(job.status) && (
                  <button
                    onClick={handleRetry}
                    className="text-sm text-purple-700 border border-purple-300 px-3 py-1 rounded-lg hover:bg-purple-50"
                  >
                    Retry
                  </button>
                )}
                {['running', 'created'].includes(job.status) && (
                  <button
                    onClick={handleCancel}
                    className="text-sm text-red-600 border border-red-300 px-3 py-1 rounded-lg hover:bg-red-50"
                  >
                    Cancel
                  </button>
                )}
                <button
                  onClick={handleDelete}
                  className="text-sm text-gray-700 border border-gray-300 px-3 py-1 rounded-lg hover:bg-gray-50"
                >
                  Delete
                </button>
              </div>
              {job.youtube_url && (
                <a
                  href={job.youtube_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm text-blue-600 underline"
                >
                  View on YouTube
                </a>
              )}
            </div>

            {/* Stage cards */}
            <div className="grid grid-cols-2 gap-3">
              {STAGES.map((stage) => {
                const s = job.stages[stage]
                return (
                  <div key={stage}>
                    <AgentStatusCard name={stage} status={s?.status as never} />
                    {!job.autonomous && (
                      <StageApproval
                        jobId={job.job_id}
                        stage={stage}
                        status={s?.status}
                        onApproved={() => fetchJob(job.job_id)}
                      />
                    )}
                  </div>
                )
              })}
            </div>

            {/* Live logs */}
            <div className="bg-white rounded-2xl shadow p-5">
              <h3 className="font-semibold text-gray-700 mb-3">Live Logs</h3>
              <LiveLogStream logs={job.logs ?? []} />
            </div>
          </>
        )}
      </div>
    </div>
  )
}
