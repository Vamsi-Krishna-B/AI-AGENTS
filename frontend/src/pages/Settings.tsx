import { useEffect, useState } from 'react'
import { getSettings, updateSettings } from '../api/client'

interface Settings {
  autonomous_mode: boolean
  schedule_time: string
  channel_id: string
  default_format: string
  generation_provider: string
  generation_model: string
  gemini_api_key?: string
  groq_api_key?: string
  youtube_client_id?: string
  youtube_client_secret?: string
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function Settings() {
  const [settings, setSettings] = useState<Settings>({
    autonomous_mode: false,
    schedule_time: '09:00',
    channel_id: '',
    default_format: 'faceless',
    generation_provider: 'gemini',
    generation_model: '',
    gemini_api_key: '',
    groq_api_key: '',
    youtube_client_id: '',
    youtube_client_secret: '',
  })
  const [saved, setSaved] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    getSettings().then((r) => setSettings((s) => ({ ...s, ...r.data })))
  }, [])

  const handleChange = (field: keyof Settings, value: string | boolean) => {
    setSettings((s) => ({ ...s, [field]: value }))
    setSaved(false)
  }

  const handleSave = async () => {
    setLoading(true)
    try {
      await updateSettings(settings as unknown as Record<string, unknown>)
      setSaved(true)
    } finally {
      setLoading(false)
    }
  }

  const handleYouTubeAuth = () => {
    window.open(`${API_BASE}/auth/youtube`, '_blank')
  }

  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-800">Settings</h1>

      <Section title="Pipeline Settings">
        <Field label="Default Video Format">
          <select
            value={settings.default_format}
            onChange={(e) => handleChange('default_format', e.target.value)}
            className="input"
          >
            <option value="faceless">Faceless (Veo AI)</option>
            <option value="avatar">Avatar (Veo AI)</option>
            <option value="animated">Animated (Veo AI)</option>
          </select>
        </Field>
        <Field label="Daily Schedule Time (UTC)">
          <input
            type="time"
            value={settings.schedule_time}
            onChange={(e) => handleChange('schedule_time', e.target.value)}
            className="input"
          />
        </Field>
        <Field label="Default Generation Provider">
          <select
            value={settings.generation_provider}
            onChange={(e) => handleChange('generation_provider', e.target.value)}
            className="input"
          >
            <option value="gemini">Gemini</option>
            <option value="groq">GROQ</option>
          </select>
        </Field>
        <Field label="Default Generation Model">
          <input
            value={settings.generation_model}
            onChange={(e) => handleChange('generation_model', e.target.value)}
            placeholder={settings.generation_provider === 'groq' ? 'llama-3.3-70b-versatile' : 'gemini-1.5-pro'}
            className="input"
          />
        </Field>
        <Field label="YouTube Channel ID">
          <input
            value={settings.channel_id}
            onChange={(e) => handleChange('channel_id', e.target.value)}
            placeholder="UCxxxxxxxxxx"
            className="input"
          />
        </Field>
      </Section>

      <Section title="API Keys">
        <Field label="Gemini API Key">
          <input
            type="password"
            value={settings.gemini_api_key ?? ''}
            onChange={(e) => handleChange('gemini_api_key', e.target.value)}
            placeholder="AIza..."
            className="input"
          />
        </Field>
        <Field label="GROQ API Key">
          <input
            type="password"
            value={settings.groq_api_key ?? ''}
            onChange={(e) => handleChange('groq_api_key', e.target.value)}
            placeholder="gsk_..."
            className="input"
          />
        </Field>
        <Field label="YouTube Client ID">
          <input
            value={settings.youtube_client_id ?? ''}
            onChange={(e) => handleChange('youtube_client_id', e.target.value)}
            className="input"
          />
        </Field>
        <Field label="YouTube Client Secret">
          <input
            type="password"
            value={settings.youtube_client_secret ?? ''}
            onChange={(e) => handleChange('youtube_client_secret', e.target.value)}
            className="input"
          />
        </Field>
      </Section>

      <Section title="YouTube OAuth">
        <p className="text-sm text-gray-500">
          Authenticate with YouTube to allow video uploads. Click below and complete the OAuth flow.
        </p>
        <button
          onClick={handleYouTubeAuth}
          className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700"
        >
          Connect YouTube Account
        </button>
      </Section>

      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={loading}
          className="px-6 py-2 bg-purple-600 text-white rounded-xl font-semibold hover:bg-purple-700 disabled:opacity-50"
        >
          {loading ? 'Saving...' : 'Save Settings'}
        </button>
        {saved && <span className="text-green-600 text-sm font-medium">Saved!</span>}
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl shadow p-5 space-y-4">
      <h2 className="text-lg font-semibold text-gray-700">{title}</h2>
      {children}
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-sm font-medium text-gray-600">{label}</label>
      {children}
    </div>
  )
}
