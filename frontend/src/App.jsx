import { useState, useRef } from 'react'
import './App.css'

/** Empty in dev (uses Vite proxy); set VITE_API_URL for production builds. */
const apiUrl = (path) =>
  `${(import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')}${path}`

const defaultUserId = import.meta.env.VITE_DEFAULT_USER_ID ?? 'usr_demo_001'

async function postChat(message, userId) {
  const res = await fetch(apiUrl('/api/chat'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, user_id: userId }),
  })
  let data = {}
  try {
    data = await res.json()
  } catch {
    /* non-JSON body */
  }
  if (!res.ok) {
    const d = data.detail ?? data.error
    const msg =
      typeof d === 'string'
        ? d
        : Array.isArray(d)
          ? d.map((x) => x.msg ?? x).join('; ')
          : res.statusText
    throw new Error(msg || 'Request failed')
  }
  if (data.error) throw new Error(data.error)
  return data.response
}

async function uploadCv(file) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('user_id', defaultUserId)

  const res = await fetch(apiUrl('/api/ingest'), {
    method: 'POST',
    body: formData,
  })

  let data = {}
  try {
    data = await res.json()
  } catch {
    /* non-JSON body */
  }

  if (!res.ok) {
    const d = data.detail ?? data.error
    const msg =
      typeof d === 'string'
        ? d
        : Array.isArray(d)
          ? d.map((x) => x.msg ?? x).join('; ')
          : res.statusText
    throw new Error(msg || 'Upload failed')
  }

  return data
}

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [cvFile, setCvFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(false)
  const fileInputRef = useRef(null)
  const bottomRef = useRef(null)

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    try {
      const result = await uploadCv(file)
      setCvFile(file.name)
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content:
            result.status === 'success'
              ? `Uploaded ${file.name}. ${result.message}`
              : `Uploaded ${file.name}, but the server returned: ${result.message}`,
        },
      ])
    } catch (err) {
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: `Upload error: ${err instanceof Error ? err.message : String(err)}`,
        },
      ])
    } finally {
      setUploading(false)
      e.target.value = ''
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    }
  }

  const handleSend = async () => {
    const text = input.trim()
    if (!text) return
    setInput('')
    const next = [...messages, { role: 'user', content: text }]
    setMessages(next)
    setLoading(true)
    try {
      const reply = await postChat(text, defaultUserId)
      setMessages([...next, { role: 'assistant', content: reply }])
    } catch (err) {
      setMessages([
        ...next,
        {
          role: 'assistant',
          content: `Error: ${err instanceof Error ? err.message : String(err)}`,
        },
      ])
    } finally {
      setLoading(false)
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="shell">
      <header className="topbar">
        <span className="logo">sirius</span>
        <span className="tagline">CV-aware AI assistant</span>
        <button
          className={`upload-btn ${cvFile ? 'uploaded' : ''}`}
          onClick={() => fileInputRef.current.click()}
          disabled={uploading}
        >
          {uploading ? 'uploading…' : cvFile ? `✓ ${cvFile}` : 'Upload CV'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          style={{ display: 'none' }}
          onChange={handleUpload}
        />
      </header>

      <main className="chat-area">
        {messages.length === 0 && (
          <div className="empty-state">
            Upload your CV, then ask anything about it.
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            <span className="bubble-label">{m.role === 'user' ? 'you' : 'sirius'}</span>
            <p>{m.content}</p>
          </div>
        ))}
        {loading && (
          <div className="bubble assistant">
            <span className="bubble-label">sirius</span>
            <p className="thinking">thinking…</p>
          </div>
        )}
        <div ref={bottomRef} />
      </main>

      <footer className="input-bar">
        <textarea
          rows={1}
          placeholder="Ask about your CV…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading || uploading}
        />
        <button onClick={handleSend} disabled={loading || uploading || !input.trim()}>
          Send
        </button>
      </footer>
    </div>
  )
}

export default App
