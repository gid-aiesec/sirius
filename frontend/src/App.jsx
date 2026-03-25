import { useState, useRef } from 'react'
import './App.css'

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
    // TODO: POST /api/ingest with FormData
    await new Promise((r) => setTimeout(r, 800)) // stub
    setCvFile(file.name)
    setUploading(false)
  }

  const handleSend = async () => {
    const text = input.trim()
    if (!text) return
    setInput('')
    const next = [...messages, { role: 'user', content: text }]
    setMessages(next)
    setLoading(true)
    // TODO: POST /api/query { query: text }
    await new Promise((r) => setTimeout(r, 1000)) // stub
    setMessages([...next, { role: 'assistant', content: '(backend not connected yet)' }])
    setLoading(false)
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
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
          accept=".pdf,.docx,.txt"
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
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>
          Send
        </button>
      </footer>
    </div>
  )
}

export default App
