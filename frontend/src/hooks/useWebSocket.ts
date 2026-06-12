import { useEffect, useRef, useState } from 'react'

const BASE_WS = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export function useWebSocket(onMessage: (data: unknown) => void) {
  const wsRef = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(`${BASE_WS}/ws`)
      wsRef.current = ws

      ws.onopen = () => setConnected(true)

      ws.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data)
          onMessage(data)
        } catch {
          // ignore
        }
      }

      ws.onclose = () => {
        setConnected(false)
        // Reconnect after 3 seconds
        setTimeout(connect, 3000)
      }

      ws.onerror = () => ws.close()
    }

    connect()
    return () => wsRef.current?.close()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const send = (data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }

  return { connected, send }
}
