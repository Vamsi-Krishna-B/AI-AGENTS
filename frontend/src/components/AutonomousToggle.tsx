interface Props {
  enabled: boolean
  onChange: (val: boolean) => void
  loading?: boolean
}

export function AutonomousToggle({ enabled, onChange, loading }: Props) {
  return (
    <div className="flex items-center gap-4">
      <span className="text-lg font-semibold text-gray-700">Autonomous Mode</span>
      <button
        disabled={loading}
        onClick={() => onChange(!enabled)}
        className={`relative inline-flex h-9 w-16 items-center rounded-full transition-colors focus:outline-none ${
          enabled ? 'bg-green-500' : 'bg-gray-300'
        } ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
      >
        <span
          className={`inline-block h-7 w-7 transform rounded-full bg-white shadow transition-transform ${
            enabled ? 'translate-x-8' : 'translate-x-1'
          }`}
        />
      </button>
      <span className={`font-medium ${enabled ? 'text-green-600' : 'text-gray-400'}`}>
        {enabled ? 'ON' : 'OFF'}
      </span>
    </div>
  )
}
