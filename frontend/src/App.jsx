import { useState, useRef, useEffect, useLayoutEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'
import logoNoBg from './assets/sirius-logo-no-bg.png'

/** Empty in dev (uses Vite proxy); set VITE_API_URL for production builds. */
const apiUrl = (path) =>
  `${(import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')}${path}`

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

// -----------------------------------------------------------------
// FITUR BARU: Fungsi untuk mengambil riwayat chat dari Supabase via Backend
// -----------------------------------------------------------------
async function fetchChatHistory(userId) {
  if (!userId) return []
  try {
    const res = await fetch(apiUrl(`/api/chat/history/${userId}`), {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })
    const data = await res.json()
    if (res.ok && data.status === 'success' && Array.isArray(data.data)) {
      // Format data Supabase ke format pesan React (role dan content)
      return data.data.map((msg) => ({
        role: msg.role,
        content: msg.content
      }))
    }
    return []
  } catch (error) {
    console.error("Failed to load chat history:", error)
    return []
  }
}

async function uploadCv(file, userId) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('user_id', userId)
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

const CV_UPLOAD_STORAGE_KEY = 'sirius_cv_upload'

function readStoredCvFilename(userId) {
  if (!userId) return null
  try {
    const raw = localStorage.getItem(CV_UPLOAD_STORAGE_KEY)
    if (!raw) return null
    const { userId: savedId, filename } = JSON.parse(raw)
    return savedId === userId && typeof filename === 'string' ? filename : null
  } catch {
    return null
  }
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

function LoginScreen({ exchanging }) {
  return (
    <div className="shell">
      <header className="topbar">
        <div className="topbar-logo">
          <div className="logo-mark-wrap">
            <img src={logoNoBg} alt="Sirius" className="header-logo" />
          </div>
        </div>
        <div className="topbar-divider" />
        <span className="tagline">Learning today. Guiding tomorrow.</span>
      </header>
      <main className="chat-area">
        <div className="empty-state">
          <div className="empty-logo-wrap">
            <img src={logoNoBg} alt="Sirius" className="empty-logo" />
          </div>
          <h1 className="empty-title">Your Career Guide</h1>
          <p className="empty-subtitle">
            Sign in with your AIESEC account to get started.
          </p>
          {exchanging ? (
            <div className="empty-hint">Signing you in…</div>
          ) : (
            <a href={apiUrl('/api/auth/login')} className="login-btn">
              Sign in with EXPA
            </a>
          )}
        </div>
      </main>
    </div>
  )
}

export default function App() {
  const [userId, setUserId] = useState(() => localStorage.getItem('user_id'))
  const [exchanging, setExchanging] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [cvFile, setCvFile] = useState(() =>
    readStoredCvFilename(localStorage.getItem('user_id')),
  )
  const [uploading, setUploading] = useState(false)
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [uploadStatusText, setUploadStatusText] = useState('Choose a PDF to upload.')
  const [uploadError, setUploadError] = useState('')
  const [loading, setLoading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  
  // State untuk melacak apakah history sedang dimuat
  const [loadingHistory, setLoadingHistory] = useState(false)

  const fileInputRef = useRef(null)
  const chatAreaRef = useRef(null)
  const textareaRef = useRef(null)

  /** Scroll chat pane to end; relies on .chat-area padding-bottom for space above the input. */
  const scrollChatToBottom = useCallback(() => {
    const el = chatAreaRef.current
    if (!el) return
    const run = () => {
      el.scrollTop = Math.max(0, el.scrollHeight - el.clientHeight)
    }
    requestAnimationFrame(() => requestAnimationFrame(run))
  }, [])

  // Handle OAuth callback: exchange ?code= for a user_id
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    if (!code) return

    window.history.replaceState({}, '', window.location.pathname)
    setExchanging(true)

    fetch(apiUrl('/api/auth/exchange'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (!data.user_id) throw new Error('No user_id returned')
        localStorage.setItem('user_id', data.user_id)
        if (data.name) localStorage.setItem('expa_name', data.name)
        setUserId(data.user_id)
      })
      .catch(() => setExchanging(false))
  }, [])

  const loadHistory = useCallback(async () => {
    if (!userId) return
    setLoadingHistory(true)
    const history = await fetchChatHistory(userId)
    if (history.length > 0) {
      setMessages(history)
    }
    setLoadingHistory(false)
  }, [userId])

  useEffect(() => {
    if (userId) {
      loadHistory()
    }
  }, [userId, loadHistory])

  useEffect(() => {
    setCvFile(readStoredCvFilename(userId))
  }, [userId])

  useLayoutEffect(() => {
    if (!userId || loadingHistory) return
    if (messages.length === 0 && !loading) return
    scrollChatToBottom()
  }, [userId, loadingHistory, messages, loading, scrollChatToBottom])

  if (!userId) return <LoginScreen exchanging={exchanging} />

  const openUploadModal = () => {
    setUploadModalOpen(true)
    setUploadStatusText('Choose a PDF to upload.')
    setUploadError('')
  }

  const handleUpload = async (file) => {
    if (!file) return
    setUploadModalOpen(true)
    if (file.type !== 'application/pdf') {
      setUploadError('Only PDF files are supported.')
      setUploadStatusText('Please choose a valid PDF file.')
      return
    }
    setUploadError('')
    setUploadStatusText(`Uploading ${file.name}...`)
    setUploading(true)
    try {
      const result = await uploadCv(file, userId)
      setCvFile(file.name)
      localStorage.setItem(
        CV_UPLOAD_STORAGE_KEY,
        JSON.stringify({ userId, filename: file.name }),
      )
      setUploadStatusText(`Upload complete: ${file.name}`)
      if (result.status === 'success') {
        setTimeout(() => setUploadModalOpen(false), 500)
      }
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : String(err))
      setUploadStatusText('Upload failed.')
    } finally {
      setUploading(false)
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
      const reply = await postChat(text, userId)
      setMessages([...next, { role: 'assistant', content: reply }])
    } catch (err) {
      setMessages([...next, {
        role: 'assistant',
        content: `Error: ${err instanceof Error ? err.message : String(err)}`,
      }])
    } finally {
      setLoading(false)
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
          onClick={openUploadModal}
          disabled={uploading}
        >
          <span className="upload-icon">{uploading ? '⟳' : cvFile ? '✓' : '↑'}</span>
          {uploading ? 'Uploading…' : cvFile ? (cvFile.length > 22 ? cvFile.slice(0, 20) + '…' : cvFile) : 'Upload CV'}
        </button>
        <input ref={fileInputRef} type="file" accept=".pdf" style={{ display: 'none' }} onChange={handleFileInput} />
      </header>

      {/* ─── CHAT ─── */}
      <main className="chat-area" ref={chatAreaRef}>
        {loadingHistory && (
          <div className="empty-hint" style={{ textAlign: 'center', marginTop: '20px' }}>
            Loading your chat history...
          </div>
        )}

        {!loadingHistory && messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-logo-wrap">
              <img src={logoNoBg} alt="Sirius" className="empty-logo" />
            </div>
            <h1 className="empty-title">Your Career Guide</h1>
            <p className="empty-subtitle">
              Upload your CV and ask anything — from tailoring it for a role to uncovering hidden strengths.
            </p>
            <div className="empty-hint" onClick={openUploadModal}>
              <span>↑</span> Drop a PDF or click to upload your CV
            </div>
          </div>
        )}

        {!loadingHistory && messages.map((m, i) => (
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

      {uploadModalOpen && (
        <div className="upload-modal-backdrop" onClick={() => !uploading && setUploadModalOpen(false)}>
          <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
            <div className="upload-modal-title">Upload CV</div>
            <div className="upload-modal-message">{uploadStatusText}</div>
            {uploadError && <div className="upload-modal-error">{uploadError}</div>}
            {uploading && (
              <div className="upload-modal-progress">
                <span className="upload-spinner" />
                <span>Processing your CV. This can take a few seconds.</span>
              </div>
            )}
            <div className="upload-modal-actions">
              <button
                className="upload-modal-btn"
                onClick={() => fileInputRef.current.click()}
                disabled={uploading}
              >
                {uploading ? 'Uploading...' : 'Choose PDF'}
              </button>
              <button
                className="upload-modal-btn secondary"
                onClick={() => setUploadModalOpen(false)}
                disabled={uploading}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}