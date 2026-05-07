import { useState, useRef } from 'react'
import { generateResponse, getDownloadUrl } from './api/client.js'

const SENSITIVE_PATTERNS = [
  { name: 'SSN', pattern: /\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b/ },
  { name: 'Credit Card', pattern: /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/ },
  { name: 'Date of Birth', pattern: /\b(DOB|date of birth|born on|birthday)[:\s]*\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b/i },
  { name: 'Phone Number', pattern: /\b(\+?1[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b/ },
  { name: 'Home Address', pattern: /\b\d{1,5}\s+([\w\s]+)(street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|lane|ln|way|court|ct|place|pl)\b/i },
]

function detectSensitiveInfo(text) {
  const found = []
  for (const { name, pattern } of SENSITIVE_PATTERNS) {
    if (pattern.test(text)) found.push(name)
  }
  return found
}

const API_BASE = import.meta.env.VITE_API_URL || '/api'

function App() {
  const [emailText, setEmailText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [toast, setToast] = useState('')
  const [feedbackSent, setFeedbackSent] = useState(false)
  const [page, setPage] = useState('app')
  const [dashData, setDashData] = useState(null)
  const [dashLoading, setDashLoading] = useState(false)
  const [templates, setTemplates] = useState([])
  const [templatesLoading, setTemplatesLoading] = useState(false)
  const [expandedTemplate, setExpandedTemplate] = useState(null)
  const [templateSearch, setTemplateSearch] = useState('')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const textareaRef = useRef(null)
  const responseRef = useRef(null)

  const sensitiveFound = detectSensitiveInfo(emailText)
  const hasSensitive = sensitiveFound.length > 0

  const showToast = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(''), 2500)
  }

  const handleGenerate = async () => {
    if (!emailText.trim() || hasSensitive) return
    setLoading(true)
    setError(null)
    setResult(null)
    setFeedbackSent(false)
    try {
      const data = await generateResponse(emailText)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleFeedback = async (type) => {
    if (!result?.query_id || feedbackSent) return
    try {
      await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_id: result.query_id, feedback: type }),
      })
      setFeedbackSent(true)
      showToast(type === 'up' ? 'Thanks for the feedback!' : 'Thanks — we\'ll work on improving this.')
    } catch {
      showToast('Failed to send feedback')
    }
  }

  const handleCopy = async () => {
    if (!responseRef.current) return
    try {
      const html = responseRef.current.innerHTML
      const plain = responseRef.current.innerText
      const blob = new Blob([html], { type: 'text/html' })
      const blobPlain = new Blob([plain], { type: 'text/plain' })
      await navigator.clipboard.write([
        new ClipboardItem({ 'text/html': blob, 'text/plain': blobPlain })
      ])
      showToast('Copied with formatting')
    } catch {
      navigator.clipboard.writeText(result?.response_text || '')
        .then(() => showToast('Copied as plain text'))
        .catch(() => showToast('Failed to copy'))
    }
  }

  const handleDownload = () => {
    if (!result?.docx_download_url) return
    window.open(getDownloadUrl(result.docx_download_url), '_blank')
  }

  const handleClear = () => {
    setEmailText('')
    setResult(null)
    setError(null)
    setFeedbackSent(false)
    textareaRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleGenerate()
  }

  const navigate = (dest) => {
    setMobileMenuOpen(false)
    if (dest === 'dashboard') {
      setPage('dashboard')
      setDashLoading(true)
      fetch(`${API_BASE}/dashboard`)
        .then(r => r.json())
        .then(data => setDashData(data))
        .catch(() => setDashData({ success: false, message: 'Failed to load dashboard' }))
        .finally(() => setDashLoading(false))
    } else if (dest === 'templates') {
      setPage('templates')
      setTemplatesLoading(true)
      setExpandedTemplate(null)
      setTemplateSearch('')
      fetch(`${API_BASE}/templates`)
        .then(r => r.json())
        .then(data => setTemplates(data.templates || []))
        .catch(() => setTemplates([]))
        .finally(() => setTemplatesLoading(false))
    } else {
      setPage('app')
    }
  }

  const filteredTemplates = templates.filter(t => {
    const title = typeof t === 'string' ? t : t.title
    return title.toLowerCase().includes(templateSearch.toLowerCase())
  })

  // ── Sidebar ──
  const renderSidebar = () => (
    <aside className={`sidebar ${mobileMenuOpen ? 'open' : ''}`}>
      <div className="sidebar-brand">
        <div className="sidebar-brand-top">
          <div className="sidebar-logo">BC</div>
          <h1>Brooklyn College</h1>
        </div>
        <p className="sidebar-brand-sub">Admissions Email Assistant</p>
      </div>

      <nav className="sidebar-nav">
        <button className={`sidebar-link ${page === 'app' ? 'active' : ''}`} onClick={() => navigate('app')}>
          <span className="sidebar-link-icon">
            <svg viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
          </span>
          Email Assistant
        </button>
        <button className={`sidebar-link ${page === 'templates' ? 'active' : ''}`} onClick={() => navigate('templates')}>
          <span className="sidebar-link-icon">
            <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          </span>
          Templates
        </button>
        <button className={`sidebar-link ${page === 'dashboard' ? 'active' : ''}`} onClick={() => navigate('dashboard')}>
          <span className="sidebar-link-icon">
            <svg viewBox="0 0 24 24"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>
          </span>
          Dashboard
        </button>
      </nav>

      <div className="sidebar-footer">
        CISC 4900 Senior Project<br/>
        Spring 2026
      </div>
    </aside>
  )

  // ── Templates Page ──
  const renderTemplates = () => (
    <div className="page-enter">
      <div className="main-header">
        <div>
          <h2>Email Response Templates</h2>
          <p>{templates.length} templates available</p>
        </div>
      </div>
      <div className="main-body">
        <input
          className="search-input"
          type="text"
          placeholder="Search templates..."
          value={templateSearch}
          onChange={(e) => setTemplateSearch(e.target.value)}
        />

        {templatesLoading && (
          <div className="loading-container">
            <div className="spinner" />
            <p className="loading-text">Loading templates...</p>
          </div>
        )}

        {!templatesLoading && filteredTemplates.length === 0 && (
          <p style={{ color: 'var(--text-muted)', fontSize: '.88rem', textAlign: 'center', padding: 32 }}>
            {templateSearch ? 'No templates match your search.' : 'No templates found.'}
          </p>
        )}

        {!templatesLoading && filteredTemplates.map((t, i) => {
          const title = typeof t === 'string' ? t : t.title
          const text = typeof t === 'string' ? '' : (t.text || '')
          const isOpen = expandedTemplate === i

          return (
            <div key={i} className="template-card">
              <div className="template-card-header" onClick={() => setExpandedTemplate(isOpen ? null : i)}>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <span className="template-number">{i + 1}</span>
                  <span className="template-card-title">
                    {title.length > 65 ? title.slice(0, 65) + '...' : title}
                  </span>
                </div>
                <span className={`template-arrow ${isOpen ? 'open' : ''}`}>▼</span>
              </div>

              {isOpen && (
                <div className="template-card-body">
                  {text ? (
                    <div className="template-preview">{text}</div>
                  ) : (
                    <p style={{ padding: '10px 0', fontSize: '.84rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                      Template content preview not available.
                    </p>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )

  // ── Dashboard Page ──
  const renderDashboard = () => (
    <div className="page-enter">
      <div className="main-header">
        <div>
          <h2>Analytics Dashboard</h2>
          <p>Track usage and performance</p>
        </div>
      </div>
      <div className="main-body">
        {dashLoading && (
          <div className="loading-container">
            <div className="spinner" />
            <p className="loading-text">Loading analytics...</p>
          </div>
        )}

        {dashData && !dashData.success && (
          <div className="error-banner">
            <span>!</span>
            <p>{dashData.message}</p>
          </div>
        )}

        {dashData && dashData.success && (
          <>
            <div className="stats-grid">
              {[
                { label: 'Total Queries', value: dashData.total_queries, color: '#882345' },
                { label: 'Matched', value: dashData.matched, color: '#2e7d4f' },
                { label: 'Unmatched', value: dashData.unmatched, color: '#c62828' },
                { label: 'Avg Confidence', value: dashData.avg_confidence, color: '#b8860b' },
                { label: 'Positive Feedback', value: dashData.thumbs_up, color: '#2e7d4f' },
                { label: 'Negative Feedback', value: dashData.thumbs_down, color: '#c62828' },
              ].map((stat, i) => (
                <div key={i} className="stat-card">
                  <p className="stat-value" style={{ color: stat.color }}>{stat.value}</p>
                  <p className="stat-label">{stat.label}</p>
                </div>
              ))}
            </div>

            <div className="card" style={{ marginBottom: 20 }}>
              <div className="card-header"><h2>Most Used Templates</h2></div>
              <div className="card-body">
                {dashData.top_templates.length === 0 && <p style={{ color: '#8a8279', fontSize: '.86rem' }}>No data yet</p>}
                {dashData.top_templates.map((t, i) => (
                  <div key={i} className="template-row">
                    <span className="template-name">{i + 1}. {t.name.length > 50 ? t.name.slice(0, 50) + '...' : t.name}</span>
                    <span className="template-count">{t.count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="card-header"><h2>Recent Queries</h2></div>
              <div className="card-body" style={{ maxHeight: 380, overflowY: 'auto' }}>
                {dashData.recent_queries.length === 0 && <p style={{ color: '#8a8279', fontSize: '.86rem' }}>No queries yet</p>}
                {dashData.recent_queries.map((q, i) => (
                  <div key={i} className="query-row">
                    <div className="query-header">
                      <span className="query-topic">{q.topic || '(no topic)'}</span>
                      <span className="query-time">{q.timestamp ? new Date(q.timestamp).toLocaleString() : ''}</span>
                    </div>
                    <div className="query-tags">
                      {q.matched ? <span className="tag-matched">Matched</span> : <span className="tag-unmatched">No match</span>}
                      {q.feedback === 'up' && <span className="tag-matched">Helpful</span>}
                      {q.feedback === 'down' && <span className="tag-unmatched">Not helpful</span>}
                      {q.confidence > 0 && <span className="tag-score">Score: {q.confidence}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )

  // ── Main App Page ──
  const renderApp = () => (
    <div className="page-enter">
      <div className="main-header">
        <div>
          <h2>Email Response Generator</h2>
          <p>Paste a student email to generate a response</p>
        </div>
      </div>
      <div className="main-body">
        <div className="app-grid">
          <div className="card">
            <div className="card-header">
              <div className="card-header-icon input">In</div>
              <div>
                <h2>Student Email</h2>
                <p>Paste the student inquiry below</p>
              </div>
            </div>
            <div className="card-body">
              <textarea
                ref={textareaRef}
                className="email-textarea"
                value={emailText}
                onChange={(e) => setEmailText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={"Paste the student's email here...\n\nExample: Hi, my name is David Brown and I applied to Brooklyn College for Fall 2026. My CUNYfirst checklist says my application is under review."}
                disabled={loading}
                style={hasSensitive ? { borderColor: '#c62828', boxShadow: '0 0 0 3px rgba(198, 40, 40, 0.15)' } : {}}
              />

              {hasSensitive && (
                <div className="sensitive-warning">
                  <div className="icon">!</div>
                  <div>
                    <p style={{ fontSize: '0.86rem', color: '#c62828', fontWeight: 600, margin: 0 }}>
                      Sensitive information detected: {sensitiveFound.join(', ')}
                    </p>
                    <p style={{ fontSize: '0.8rem', color: '#5a534d', margin: '4px 0 0 0' }}>
                      Please remove all personal information before processing.
                    </p>
                  </div>
                </div>
              )}

              <div className="btn-row">
                <button className="btn btn-primary" onClick={handleGenerate} disabled={loading || !emailText.trim() || hasSensitive}>
                  {loading ? 'Generating...' : 'Generate Response'}
                </button>
                <button className="btn btn-secondary" onClick={handleClear} disabled={loading}>Clear</button>
              </div>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 8, fontStyle: 'italic' }}>
                Ctrl+Enter to generate
              </p>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-header-icon output">Out</div>
              <div>
                <h2>Generated Response</h2>
                <p>Ready to copy and paste into your email</p>
              </div>
            </div>
            <div className="card-body">
              {error && (
                <div className="error-banner"><span>!</span><p>{error}</p></div>
              )}

              {loading && (
                <div className="loading-container">
                  <div className="spinner" />
                  <p className="loading-text">Finding the best template...</p>
                </div>
              )}

              {result && !result.success && (
                <div className="no-match">
                  <div className="no-match-icon">!</div>
                  <h3>No Matching Template Found</h3>
                  <p>This email may need a manual response. Topic: <strong>{result.student_topic}</strong></p>
                </div>
              )}

              {result && result.success && (
                <>
                  <div className="response-meta">
                    <span className="meta-tag template">{result.template_title.length > 40 ? result.template_title.slice(0, 40) + '...' : result.template_title}</span>
                    {result.student_name && result.student_name !== '(not found)' && (
                      <span className="meta-tag name">{result.student_name}</span>
                    )}
                    {result.student_semester && result.student_semester !== '(not specified)' && (
                      <span className="meta-tag semester">{result.student_semester}</span>
                    )}
                  </div>
                  <div ref={responseRef} className="response-text" dangerouslySetInnerHTML={{ __html: result.response_html }} />
                  <div className="response-actions">
                    <button className="btn btn-primary" onClick={handleCopy}>Copy with Formatting</button>
                    <button className="btn btn-gold" onClick={handleDownload}>Download DOCX</button>
                  </div>
                  <div className="feedback-row">
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Was this response helpful?</span>
                    {feedbackSent ? (
                      <span style={{ fontSize: '0.8rem', color: 'var(--success)', fontWeight: 500 }}>Thank you for your feedback</span>
                    ) : (
                      <>
                        <button className="feedback-btn" onClick={() => handleFeedback('up')}>Yes</button>
                        <button className="feedback-btn" onClick={() => handleFeedback('down')}>No</button>
                      </>
                    )}
                  </div>
                </>
              )}

              {!loading && !result && !error && (
                <div className="empty-state">
                  <div className="empty-state-icon">
                    <svg viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                  </div>
                  <h3>No response yet</h3>
                  <p>Paste a student email on the left and click Generate Response to get started.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="app-layout">
      <button className="mobile-menu-btn" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
        {mobileMenuOpen ? '✕' : '☰'}
      </button>
      {renderSidebar()}
      <div className="main-content">
        {page === 'app' && renderApp()}
        {page === 'templates' && renderTemplates()}
        {page === 'dashboard' && renderDashboard()}
      </div>
      <div className={`toast ${toast ? 'show' : ''}`}>{toast}</div>
    </div>
  )
}

export default App