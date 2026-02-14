import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import Prism from 'prismjs'
import 'prismjs/themes/prism-tomorrow.css'
import 'prismjs/components/prism-bash'
import { FiSend, FiCopy, FiCheck, FiLogOut } from 'react-icons/fi'
import { SiArchlinux } from 'react-icons/si'
import { useAuth } from '../context/AuthContext'
import Sidebar from '../components/Sidebar'
import './Chat.css'

function Chat() {
  const { user, token, logout } = useAuth()
  const navigate = useNavigate()
  
  const [sessions, setSessions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [loadingStatus, setLoadingStatus] = useState('')
  const [abortController, setAbortController] = useState(null)
  const [copiedIndex, setCopiedIndex] = useState(null)
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    Prism.highlightAll()
  }, [messages])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [input])

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      const response = await fetch('/api/sessions', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setSessions(data)
        if (data.length > 0 && !currentSessionId) {
          setCurrentSessionId(data[0].id)
          loadSessionMessages(data[0].id)
        }
      }
    } catch (error) {
      console.error('Failed to load sessions:', error)
    }
  }

  const loadSessionMessages = async (sessionId) => {
    try {
      const response = await fetch(`/api/sessions/${sessionId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setMessages(data.messages)
      }
    } catch (error) {
      console.error('Failed to load messages:', error)
    }
  }

  const handleCreateSession = async () => {
    try {
      const response = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const newSession = await response.json()
        setSessions([newSession, ...sessions])
        setCurrentSessionId(newSession.id)
        setMessages([])
      }
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }

  const handleSelectSession = async (sessionId) => {
    setCurrentSessionId(sessionId)
    await loadSessionMessages(sessionId)
  }

  const handleDeleteSession = async (sessionId) => {
    try {
      const response = await fetch(`/api/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        setSessions(sessions.filter(s => s.id !== sessionId))
        if (currentSessionId === sessionId) {
          const remaining = sessions.filter(s => s.id !== sessionId)
          if (remaining.length > 0) {
            setCurrentSessionId(remaining[0].id)
            loadSessionMessages(remaining[0].id)
          } else {
            setCurrentSessionId(null)
            setMessages([])
          }
        }
      }
    } catch (error) {
      console.error('Failed to delete session:', error)
    }
  }

  const handleRenameSession = async (sessionId, newTitle) => {
    try {
      const response = await fetch(`/api/sessions/${sessionId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ title: newTitle })
      })
      if (response.ok) {
        setSessions(sessions.map(s => 
          s.id === sessionId ? { ...s, title: newTitle } : s
        ))
      }
    } catch (error) {
      console.error('Failed to rename session:', error)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    // Create new session if none exists
    let sessionId = currentSessionId
    if (!sessionId) {
      const response = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const newSession = await response.json()
        sessionId = newSession.id
        setCurrentSessionId(sessionId)
        setSessions([newSession, ...sessions])
      }
    }

    const userMessage = { role: 'user', content: input }
    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInput('')
    setIsLoading(true)
    setLoadingStatus('Thinking...')

    const assistantMessage = { role: 'assistant', content: '' }
    setMessages([...newMessages, assistantMessage])

    // Create abort controller for this request
    const controller = new AbortController()
    setAbortController(controller)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          messages: newMessages,
          model: 'llama3.2',
          session_id: sessionId
        }),
        signal: controller.signal
      })

      setLoadingStatus('Generating response...')
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let firstChunk = true

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        if (firstChunk) {
          setLoadingStatus('')
          firstChunk = false
        }

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.error) {
                assistantMessage.content += `\n**Error:** ${data.error}`
              } else if (data.message?.content) {
                assistantMessage.content += data.message.content
              }
              setMessages([...newMessages, { ...assistantMessage }])
            } catch (e) {
              console.error('Parse error:', e)
            }
          }
        }
      }
      
      // Reload sessions to update message count
      loadSessions()
    } catch (error) {
      if (error.name === 'AbortError') {
        assistantMessage.content = '**Response stopped by user**'
      } else {
        assistantMessage.content = `**Error:** ${error.message}`
      }
      setMessages([...newMessages, assistantMessage])
    } finally {
      setIsLoading(false)
      setLoadingStatus('')
      setAbortController(null)
    }
  }

  const stopResponse = () => {
    if (abortController) {
      abortController.abort()
      setIsLoading(false)
      setLoadingStatus('')
      setAbortController(null)
    }
  }

  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text)
    setCopiedIndex(index)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  return (
    <div className="app">
      <header>
        <div className="header-content">
          <SiArchlinux className="arch-logo" />
          <h1>Archy - Your Arch Linux Assistant</h1>
        </div>
        <div className="header-actions">
          <span className="user-info">{user?.username || user?.email}</span>
          <button onClick={handleLogout} className="logout-btn" title="Logout">
            <FiLogOut />
          </button>
        </div>
      </header>

      <div className="chat-layout">
        <Sidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={handleSelectSession}
          onCreateSession={handleCreateSession}
          onDeleteSession={handleDeleteSession}
          onRenameSession={handleRenameSession}
        />

        <main>
          <div className="messages">
            <AnimatePresence>
              {messages.map((msg, idx) => (
                <motion.div
                  key={idx}
                  className={`message ${msg.role}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="message-header">
                    <span className="role-badge">{msg.role === 'user' ? 'You' : 'Archy'}</span>
                  </div>
                  <div className="message-content">
                    <ReactMarkdown
                      components={{
                        code({ node, inline, className, children, ...props }) {
                          const match = /language-(\w+)/.exec(className || '')
                          const codeString = String(children).replace(/\n$/, '')
                          
                          return !inline && match ? (
                            <div className="code-block">
                              <div className="code-header">
                                <span className="language-badge">{match[1]}</span>
                                <button
                                  onClick={() => copyToClipboard(codeString, idx)}
                                  className="copy-btn"
                                >
                                  {copiedIndex === idx ? <FiCheck /> : <FiCopy />}
                                  {copiedIndex === idx ? ' Copied!' : ' Copy'}
                                </button>
                              </div>
                              <pre>
                                <code className={className} {...props}>
                                  {children}
                                </code>
                              </pre>
                            </div>
                          ) : (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          )
                        }
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            
            {/* Loading Skeleton */}
            {isLoading && loadingStatus && (
              <motion.div 
                className="loading-skeleton"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <div className="skeleton-avatar">
                  <SiArchlinux className="skeleton-icon" />
                </div>
                <div className="skeleton-content">
                  <div className="skeleton-status">
                    <span className="skeleton-dots"></span>
                    {loadingStatus}
                  </div>
                  <div className="skeleton-lines">
                    <div className="skeleton-line skeleton-line-1"></div>
                    <div className="skeleton-line skeleton-line-2"></div>
                    <div className="skeleton-line skeleton-line-3"></div>
                  </div>
                </div>
              </motion.div>
            )}
            
            {isLoading && !loadingStatus && (
              <motion.div
                className="typing-indicator"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <span></span>
                <span></span>
                <span></span>
              </motion.div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          <div className="input-area">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  sendMessage()
                }
              }}
              placeholder="Ask Archy anything about Arch Linux..."
              disabled={isLoading}
              rows="1"
            />
            {isLoading ? (
              <button onClick={stopResponse} className="stop-btn" title="Stop response">
                <span className="stop-icon">■</span>
              </button>
            ) : (
              <button 
                onClick={sendMessage} 
                disabled={isLoading || !input.trim()}
                className="send-btn"
              >
                <FiSend />
              </button>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

export default Chat
