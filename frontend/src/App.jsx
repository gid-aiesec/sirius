import { useState, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'
import logoNoBg from './assets/sirius-logo-no-bg.png'

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

function MessageContent({ role, content }) {
  if (role === 'user') return content

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ node, ...props }) => <a {...props} target="_blank" rel="noreferrer" />,
      }}
    >
      {content}
    </ReactMarkdown>
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
      {/* ─── DRAG OVERLAY ─── */}
      {dragOver && (
        <div className="drag-overlay">
          <img src={logoNoBg} alt="Sirius" className="drag-overlay-logo" />
          <span className="drag-overlay-text">Drop your CV here</span>
        </div>
      )}

      {/* ─── HEADER ─── */}
      <header className="topbar">
        <div className="topbar-logo">
          <div className="logo-mark-wrap">
            <img src={logoNoBg} alt="Sirius" className="header-logo" />
          </div>
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

      {/* ─── CHAT ─── */}
      <main className="chat-area">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-logo-wrap">
              <img src={logoNoBg} alt="Sirius" className="empty-logo" />
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
            <div className="bubble-body">
              <MessageContent role={m.role} content={m.content} />
            </div>
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

      {/* ─── INPUT ─── */}
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
