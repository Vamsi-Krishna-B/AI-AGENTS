import { useEffect, useRef } from 'react'

interface LogEntry {
  agent: string
  level: string
  message: string
  timestamp: string
}

interface Props {
  logs: LogEntry[]
}

const LEVEL_COLOR: Record<string, string> = {
  INFO: 'text-green-400',
  WARNING: 'text-yellow-400',
  ERROR: 'text-red-400',
}

export function LiveLogStream({ logs }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  return (
    <div className="bg-gray-900 text-gray-100 rounded-lg p-3 h-64 overflow-y-auto font-mono text-xs">
      {logs.length === 0 && (
        <span className="text-gray-500">Waiting for logs...</span>
      )}
      {logs.map((log, i) => (
        <div key={i} className="mb-0.5">
          <span className="text-gray-500">{new Date(log.timestamp).toLocaleTimeString()}</span>{' '}
          <span className="text-purple-400">[{log.agent}]</span>{' '}
          <span className={LEVEL_COLOR[log.level] ?? 'text-gray-300'}>{log.level}</span>{' '}
          <span>{log.message}</span>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
