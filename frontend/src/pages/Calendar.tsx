import { useEffect, useState } from 'react'
import { listJobs } from '../api/client'

interface Job {
  job_id: string
  status: string
  created_at: string
  stages: {
    research?: { output?: { title?: string } }
    upload?: { output?: { scheduled_publish_time?: string; youtube_url?: string } }
  }
}

function getDaysInMonth(year: number, month: number) {
  return new Date(year, month + 1, 0).getDate()
}

function getFirstDayOfMonth(year: number, month: number) {
  return new Date(year, month, 1).getDay()
}

export function Calendar() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [today] = useState(new Date())
  const [viewYear, setViewYear] = useState(today.getFullYear())
  const [viewMonth, setViewMonth] = useState(today.getMonth())

  useEffect(() => {
    listJobs().then((r) => setJobs(r.data))
  }, [])

  const daysInMonth = getDaysInMonth(viewYear, viewMonth)
  const firstDay = getFirstDayOfMonth(viewYear, viewMonth)

  const jobsByDay: Record<number, Job[]> = {}
  for (const job of jobs) {
    const d = new Date(
      job.stages?.upload?.output?.scheduled_publish_time ?? job.created_at
    )
    if (d.getFullYear() === viewYear && d.getMonth() === viewMonth) {
      const day = d.getDate()
      if (!jobsByDay[day]) jobsByDay[day] = []
      jobsByDay[day].push(job)
    }
  }

  const prevMonth = () => {
    if (viewMonth === 0) { setViewMonth(11); setViewYear((y) => y - 1) }
    else setViewMonth((m) => m - 1)
  }
  const nextMonth = () => {
    if (viewMonth === 11) { setViewMonth(0); setViewYear((y) => y + 1) }
    else setViewMonth((m) => m + 1)
  }

  const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  const DAY_NAMES = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-800">Content Calendar</h1>
        <div className="flex items-center gap-2 ml-auto">
          <button onClick={prevMonth} className="px-3 py-1 rounded-lg border hover:bg-gray-100 text-sm">←</button>
          <span className="font-semibold text-gray-700">{MONTH_NAMES[viewMonth]} {viewYear}</span>
          <button onClick={nextMonth} className="px-3 py-1 rounded-lg border hover:bg-gray-100 text-sm">→</button>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow p-4">
        <div className="grid grid-cols-7 gap-1 mb-2">
          {DAY_NAMES.map((d) => (
            <div key={d} className="text-center text-xs font-semibold text-gray-400 py-1">{d}</div>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-1">
          {Array.from({ length: firstDay }).map((_, i) => (
            <div key={`empty-${i}`} />
          ))}
          {Array.from({ length: daysInMonth }).map((_, i) => {
            const day = i + 1
            const dayJobs = jobsByDay[day] ?? []
            const isToday =
              day === today.getDate() &&
              viewMonth === today.getMonth() &&
              viewYear === today.getFullYear()
            return (
              <div
                key={day}
                className={`min-h-[70px] rounded-lg p-1 border text-xs ${
                  isToday ? 'border-purple-400 bg-purple-50' : 'border-gray-100'
                }`}
              >
                <div className={`font-semibold mb-1 ${isToday ? 'text-purple-600' : 'text-gray-600'}`}>{day}</div>
                {dayJobs.map((j) => (
                  <div
                    key={j.job_id}
                    className="bg-purple-100 text-purple-800 rounded px-1 mb-0.5 truncate"
                    title={j.stages?.research?.output?.title ?? j.job_id}
                  >
                    {j.stages?.research?.output?.title ?? j.job_id.slice(0, 6)}
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
