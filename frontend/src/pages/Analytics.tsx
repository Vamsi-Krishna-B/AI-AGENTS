import { useEffect, useState } from 'react'
import { getAnalytics } from '../api/client'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'

interface AnalyticsItem {
  video_id: string
  title?: string
  youtube_url: string
  views: number
  likes: number
  comments: number
}

export function Analytics() {
  const [data, setData] = useState<AnalyticsItem[]>([])
  const [loading, setLoading] = useState(false)

  const fetch = async (refresh = false) => {
    setLoading(true)
    try {
      const res = await getAnalytics(refresh)
      setData(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetch() }, [])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Analytics</h1>
        <button
          onClick={() => fetch(true)}
          disabled={loading}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 disabled:opacity-50"
        >
          {loading ? 'Refreshing...' : '↻ Refresh from YouTube'}
        </button>
      </div>

      {data.length === 0 ? (
        <p className="text-gray-400">No analytics data yet. Run a job and refresh after upload.</p>
      ) : (
        <>
          {/* Views chart */}
          <div className="bg-white rounded-2xl shadow p-5">
            <h2 className="text-lg font-semibold text-gray-700 mb-3">Views per Video</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data} margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="video_id" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="views" fill="#7c3aed" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Likes/Comments chart */}
          <div className="bg-white rounded-2xl shadow p-5">
            <h2 className="text-lg font-semibold text-gray-700 mb-3">Likes & Comments</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data} margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="video_id" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="likes" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="comments" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Table */}
          <div className="bg-white rounded-2xl shadow p-5 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 border-b">
                  <th className="pb-2">Title / ID</th>
                  <th className="pb-2">Views</th>
                  <th className="pb-2">Likes</th>
                  <th className="pb-2">Comments</th>
                  <th className="pb-2">Link</th>
                </tr>
              </thead>
              <tbody>
                {data.map((item) => (
                  <tr key={item.video_id} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="py-2 text-gray-700">{item.title ?? item.video_id}</td>
                    <td className="py-2">{item.views.toLocaleString()}</td>
                    <td className="py-2">{item.likes.toLocaleString()}</td>
                    <td className="py-2">{item.comments.toLocaleString()}</td>
                    <td className="py-2">
                      <a href={item.youtube_url} target="_blank" rel="noreferrer" className="text-blue-600 underline text-xs">
                        YouTube
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
