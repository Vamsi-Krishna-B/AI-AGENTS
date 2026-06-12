interface Props {
  name: string
  status: 'pending' | 'awaiting_approval' | 'approved' | 'running' | 'done' | 'failed'
  timeTaken?: number | null
  output?: unknown
}

const STATUS_COLOR: Record<string, string> = {
  pending: 'bg-gray-200 text-gray-600',
  awaiting_approval: 'bg-yellow-100 text-yellow-700',
  approved: 'bg-blue-100 text-blue-700',
  running: 'bg-blue-200 text-blue-800 animate-pulse',
  done: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
}

export function AgentStatusCard({ name, status, timeTaken }: Props) {
  const colorClass = STATUS_COLOR[status] ?? 'bg-gray-100 text-gray-500'
  return (
    <div className={`rounded-xl p-4 shadow-sm border flex flex-col gap-1 ${colorClass}`}>
      <div className="flex items-center justify-between">
        <span className="font-semibold capitalize">{name.replace('_', ' ')}</span>
        <span className="text-xs uppercase tracking-wide">{status}</span>
      </div>
      {timeTaken != null && (
        <span className="text-xs opacity-70">{timeTaken.toFixed(1)}s</span>
      )}
    </div>
  )
}
