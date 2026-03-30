import { useState, useRef } from 'react'
import { generateResponse, getDownloadUrl } from './api/client.js'

function App() {
  const [emailText, setEmailText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [toast, setToast] = useState('')
  const textareaRef = useRef(null)

  const showToast = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(''), 2500)
  }

  const handleGenerate = async () => {
    if (!emailText.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await generateResponse(emailText)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    if (!result?.response_text) return
    navigator.clipboard.writeText(result.response_text)
      .then(() => showToast('Copied to clipboard'))
      .catch(() => showToast('Failed to copy'))
  }

  const handleDownload = () => {
    if (!result?.docx_download_url) return
    window.open(getDownloadUrl(result.docx_download_url), '_blank')
  }

  const handleClear = () => {
    setEmailText('')
    setResult(null)
    setError(null)
    textareaRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleGenerate()
  }

  return (
    <>
      <header className="header">
        <div className="header-top">
          <span>City University of New York</span>
          <span style={{ opacity: 0.4 }}>|</span>
          <span>Office of Undergraduate Admissions</span>
        </div>
        <div className="header-main">
          <div className="header-brand">
            <div className="header-logo">BC</div>
            <div className="header-text">
              <h1>Brooklyn College</h1>
              <p>Admissions Email Assistant</p>
            </div>
          </div>
          <div className="header-badge">AI-Powered</div>
        </div>
      </header>

      <main className="app-container">
        <div className="card">
          <div className="card-header">
            <div className="card-header-icon input">✉</div>
            <div>
              <h2>Student Email</h2>
              <p>Paste the student's inquiry below</p>
            </div>
          </div>
          <div className="card-body">
            <textarea
              ref={textareaRef}
              className="email-textarea"
              value={emailText}
              onChange={(e) => setEmailText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={"Paste the student's email here...\n\nExample: Hi, my name is Sarah Chen and I applied to Brooklyn College for Fall 2026. My CUNYfirst checklist says my application is under review."}
              disabled={loading}
            />
            <div className="btn-row">
              <button className="btn btn-primary" onClick={handleGenerate} disabled={loading || !emailText.trim()}>
                {loading ? 'Generating...' : 'Generate Response'}
              </button>
              <button className="btn btn-secondary" onClick={handleClear} disabled={loading}>
                Clear
              </button>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 10, fontStyle: 'italic' }}>
              Press Ctrl+Enter to generate quickly
            </p>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-header-icon output">✓</div>
            <div>
              <h2>Generated Response</h2>
              <p>Ready to copy and paste into your email</p>
            </div>
          </div>
          <div className="card-body">
            {error && (
              <div className="error-banner">
                <span>⚠</span>
                <p>{error}</p>
              </div>
            )}

            {loading && (
              <div className="loading-container">
                <div className="spinner" />
                <p className="loading-text">Finding the best template...</p>
              </div>
            )}

            {result && !result.success && (
              <div className="no-match">
                <div className="no-match-icon">⚠️</div>
                <h3>No Matching Template Found</h3>
                <p>This email may need a manual response. Topic: <strong>{result.student_topic}</strong></p>
              </div>
            )}

            {result && result.success && (
              <>
                <div className="response-meta">
                  <span className="meta-tag template">
                    📋 {result.template_title.length > 45 ? result.template_title.slice(0, 45) + '...' : result.template_title}
                  </span>
                  {result.student_name && result.student_name !== '(not found)' && (
                    <span className="meta-tag name">👤 {result.student_name}</span>
                  )}
                  {result.student_semester && result.student_semester !== '(not specified)' && (
                    <span className="meta-tag semester">📅 {result.student_semester}</span>
                  )}
                </div>
                <div className="response-text">{result.response_text}</div>
                <div className="response-actions">
                  <button className="btn btn-primary" onClick={handleCopy}>📋 Copy to Clipboard</button>
                  <button className="btn btn-gold" onClick={handleDownload}>⬇ Download DOCX</button>
                </div>
              </>
            )}

            {!loading && !result && !error && (
              <div className="empty-state">
                <div className="empty-state-icon">📬</div>
                <h3>No response yet</h3>
                <p>Paste a student email on the left and click Generate Response.</p>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="footer">
        Brooklyn College — Office of Undergraduate Admissions<br />
        CISC 4900 Senior Project — Spring 2026
      </footer>

      <div className={`toast ${toast ? 'show' : ''}`}>{toast}</div>
    </>
  )
}

export default App
