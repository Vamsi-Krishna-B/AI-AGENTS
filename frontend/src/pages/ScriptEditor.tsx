import { useEffect, useState } from 'react'
import { listJobs, getJob } from '../api/client'

interface Scene {
  scene_number: number
  type: string
  duration_seconds: number
  script_text: string
  visual_description: string
  b_roll_query: string
}

interface ScriptData {
  full_script: string
  scenes: Scene[]
  estimated_duration: number
  voiceover_text: string
}

interface Job {
  job_id: string
  status: string
  stages: {
    research?: { output?: { title?: string } }
    script?: { output?: ScriptData }
  }
}

export function ScriptEditor() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [job, setJob] = useState<Job | null>(null)
  const [editedScenes, setEditedScenes] = useState<Scene[]>([])

  useEffect(() => {
    listJobs().then((r) => setJobs(r.data))
  }, [])

  useEffect(() => {
    if (!selectedId) return
    getJob(selectedId).then((r) => {
      setJob(r.data)
      setEditedScenes(r.data.stages?.script?.output?.scenes ?? [])
    })
  }, [selectedId])

  const handleSceneChange = (idx: number, field: keyof Scene, value: string | number) => {
    setEditedScenes((prev) => {
      const updated = [...prev]
      updated[idx] = { ...updated[idx], [field]: value }
      return updated
    })
  }

  const scriptOutput = job?.stages?.script?.output
  const title = job?.stages?.research?.output?.title ?? 'No title'

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-800">Script Editor</h1>
        <select
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm text-gray-700"
        >
          <option value="">— Select Job —</option>
          {jobs
            .filter((j) => j.stages?.script?.output)
            .map((j) => (
              <option key={j.job_id} value={j.job_id}>
                {j.job_id.slice(0, 8)} ({j.status})
              </option>
            ))}
        </select>
      </div>

      {!scriptOutput ? (
        <p className="text-gray-400">Select a job with a completed script stage.</p>
      ) : (
        <>
          <div className="bg-white rounded-2xl shadow p-5">
            <h2 className="text-lg font-semibold text-gray-700 mb-1">{title}</h2>
            <p className="text-xs text-gray-400">
              Estimated duration: {scriptOutput.estimated_duration}s
            </p>
            <div className="mt-3">
              <label className="text-sm font-medium text-gray-600">Full Script</label>
              <pre className="mt-1 text-xs text-gray-700 whitespace-pre-wrap bg-gray-50 rounded p-3 max-h-40 overflow-y-auto">
                {scriptOutput.full_script}
              </pre>
            </div>
          </div>

          <h3 className="text-lg font-semibold text-gray-700">Scenes</h3>
          <div className="space-y-4">
            {editedScenes.map((scene, idx) => (
              <div key={scene.scene_number} className="bg-white rounded-2xl shadow p-5 space-y-3">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-purple-600">Scene {scene.scene_number}</span>
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                    {scene.type}
                  </span>
                  <span className="text-xs text-gray-400">{scene.duration_seconds}s</span>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500">Script Text</label>
                  <textarea
                    value={scene.script_text}
                    onChange={(e) => handleSceneChange(idx, 'script_text', e.target.value)}
                    rows={3}
                    className="w-full mt-1 border rounded-lg p-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-300"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500">Visual Description</label>
                  <input
                    value={scene.visual_description}
                    onChange={(e) => handleSceneChange(idx, 'visual_description', e.target.value)}
                    className="w-full mt-1 border rounded-lg p-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-300"
                  />
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
