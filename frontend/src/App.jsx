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
  try { data = await res.json() } catch { /* non-JSON body */ }
  if (!res.ok) {
    const d = data.detail ?? data.error
    const msg = typeof d === 'string' ? d : Array.isArray(d) ? d.map((x) => x.msg ?? x).join('; ') : res.statusText
    throw new Error(msg || 'Request failed')
  }
  if (data.error) throw new Error(data.error)
  return data.response
}

async function uploadCv(file) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('user_id', defaultUserId)
  const res = await fetch(apiUrl('/api/ingest'), { method: 'POST', body: formData })
  let data = {}
  try { data = await res.json() } catch { /* non-JSON body */ }
  if (!res.ok) {
    const d = data.detail ?? data.error
    const msg = typeof d === 'string' ? d : Array.isArray(d) ? d.map((x) => x.msg ?? x).join('; ') : res.statusText
    throw new Error(msg || 'Upload failed')
  }
  return data
}

const SiriusLogoMark = ({ size = 32 }) => (
  <svg width={size} height={size} viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="starGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#38bdf8" />
        <stop offset="100%" stopColor="#818cf8" />
      </linearGradient>
    </defs>
    <path d="M60 10 L68 52 L110 60 L68 68 L60 110 L52 68 L10 60 L52 52 Z" fill="url(#starGrad)" opacity="0.95" />
    <ellipse cx="60" cy="70" rx="38" ry="18" stroke="url(#starGrad)" strokeWidth="1.5" strokeDasharray="4 3" fill="none" transform="rotate(-20 60 70)" opacity="0.7" />
    <circle cx="92" cy="52" r="4"   fill="#38bdf8" opacity="0.9" />
    <circle cx="98" cy="65" r="3"   fill="#818cf8" opacity="0.8" />
    <circle cx="30" cy="78" r="3.5" fill="#38bdf8" opacity="0.8" />
    <circle cx="36" cy="90" r="2.5" fill="#818cf8" opacity="0.7" />
  </svg>
)

function StarField() {
  const stars = Array.from({ length: 60 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 1.5 + 0.5,
    opacity: Math.random() * 0.5 + 0.1,
    delay: Math.random() * 4,
    duration: Math.random() * 3 + 2,
  }))

  return (
    <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', overflow: 'hidden', zIndex: 0 }}>
      {stars.map(s => (
        <div
          key={s.id}
          style={{
            position: 'absolute',
            left: `${s.x}%`,
            top: `${s.y}%`,
            width: `${s.size}px`,
            height: `${s.size}px`,
            borderRadius: '50%',
            background: s.id % 3 === 0 ? '#38bdf8' : s.id % 3 === 1 ? '#818cf8' : '#e2e8f0',
            opacity: s.opacity,
            animation: `twinkle ${s.duration}s ${s.delay}s ease-in-out infinite alternate`,
          }}
        />
      ))}
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [cvFile, setCvFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef(null)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  const handleUpload = async (file) => {
    if (!file || file.type !== 'application/pdf') return
    setUploading(true)
    try {
      const result = await uploadCv(file)
      setCvFile(file.name)
      setMessages((cur) => [...cur, {
        role: 'assistant',
        content: result.status === 'success'
          ? `CV uploaded — ${file.name}. ${result.message}`
          : `Uploaded ${file.name}, but the server returned: ${result.message}`,
      }])
    } catch (err) {
      setMessages((cur) => [...cur, {
        role: 'assistant',
        content: `Upload error: ${err instanceof Error ? err.message : String(err)}`,
      }])
    } finally {
      setUploading(false)
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    }
  }

  const handleFileInput = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    await handleUpload(file)
    e.target.value = ''
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    await handleUpload(file)
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
      setMessages([...next, {
        role: 'assistant',
        content: `Error: ${err instanceof Error ? err.message : String(err)}`,
      }])
    } finally {
      setLoading(false)
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const handleInput = (e) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'
  }

  return (
    <div
      className="shell"
      onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      <StarField />

      {dragOver && (
        <div className="drag-overlay">
          <SiriusLogoMark size={56} />
          <span className="drag-overlay-text">Drop your CV here</span>
        </div>
      )}

      <header className="topbar">
        <div className="topbar-logo">
          <div className="logo-mark-wrap">
            <SiriusLogoMark size={34} />
          </div>
          <span className="logo-text">SIRIUS</span>
        </div>
        <div className="topbar-divider" />
        <span className="tagline">Learning today. Guiding tomorrow.</span>
        <div className="topbar-spacer" />
        <button
          className={`upload-btn ${cvFile ? 'uploaded' : ''}`}
          onClick={() => fileInputRef.current.click()}
          disabled={uploading}
        >
          <span className="upload-icon">{uploading ? '⟳' : cvFile ? '✓' : '↑'}</span>
          {uploading ? 'Uploading…' : cvFile ? (cvFile.length > 22 ? cvFile.slice(0, 20) + '…' : cvFile) : 'Upload CV'}
        </button>
        <input ref={fileInputRef} type="file" accept=".pdf" style={{ display: 'none' }} onChange={handleFileInput} />
      </header>

      <main className="chat-area">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-logo-wrap">
              <SiriusLogoMark size={72} />
            </div>
            <h1 className="empty-title">Your Career Guide</h1>
            <p className="empty-subtitle">
              Upload your CV and ask anything — from tailoring it for a role to uncovering hidden strengths.
            </p>
            <div className="empty-hint" onClick={() => fileInputRef.current.click()}>
              <span>↑</span> Drop a PDF or click to upload your CV
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            <span className="bubble-label">{m.role === 'user' ? 'you' : 'sirius'}</span>
            <div className="bubble-body">{m.content}</div>
          </div>
        ))}

        {loading && (
          <div className="bubble assistant">
            <span className="bubble-label">sirius</span>
            <div className="bubble-body">
              <div className="thinking">
                <span>Thinking</span>
                <div className="thinking-dots">
                  <div className="thinking-dot" />
                  <div className="thinking-dot" />
                  <div className="thinking-dot" />
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </main>

      <footer className="input-bar">
        <div className="input-wrap">
          <textarea
            ref={textareaRef}
            rows={1}
            placeholder="Ask about your CV…"
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            disabled={loading || uploading}
          />
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={loading || uploading || !input.trim()}
          >
            ↑
          </button>
        </div>
        <div className="input-footer">Shift+Enter for new line · PDF only</div>
      </footer>
    </div>
  )
}