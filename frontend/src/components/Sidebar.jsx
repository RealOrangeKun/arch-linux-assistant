import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiPlus, FiMessageSquare, FiTrash2, FiEdit2, FiCheck, FiX, FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import './Sidebar.css';

export default function Sidebar({ 
  sessions, 
  currentSessionId, 
  onSelectSession, 
  onCreateSession, 
  onDeleteSession, 
  onRenameSession 
}) {
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleStartEdit = (session) => {
    setEditingId(session.id);
    setEditTitle(session.title);
  };

  const handleSaveEdit = async (sessionId) => {
    if (editTitle.trim()) {
      await onRenameSession(sessionId, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditTitle('');
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <motion.div 
      className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}
      animate={{ width: isCollapsed ? '60px' : '280px' }}
      transition={{ duration: 0.3 }}
    >
      <div className="sidebar-header">
        {!isCollapsed && <h2>Chats</h2>}
        <div className="header-buttons">
          {!isCollapsed && (
            <button onClick={onCreateSession} className="new-chat-btn" title="New Chat">
              <FiPlus />
            </button>
          )}
          <button 
            onClick={() => setIsCollapsed(!isCollapsed)} 
            className="collapse-btn"
            title={isCollapsed ? 'Expand' : 'Collapse'}
          >
            {isCollapsed ? <FiChevronRight /> : <FiChevronLeft />}
          </button>
        </div>
      </div>

      {isCollapsed ? (
        <div className="collapsed-sessions">
          <button onClick={onCreateSession} className="collapsed-new-btn" title="New Chat">
            <FiPlus />
          </button>
          {sessions.map((session) => (
            <button
              key={session.id}
              className={`collapsed-session-item ${currentSessionId === session.id ? 'active' : ''}`}
              onClick={() => onSelectSession(session.id)}
              title={session.title}
            >
              <FiMessageSquare />
            </button>
          ))}
        </div>
      ) : (
        <div className="session-list">
          <AnimatePresence>
            {sessions.length === 0 ? (
              <motion.div
                className="empty-state"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <FiMessageSquare />
                <p>No chats yet</p>
                <span>Start a new conversation</span>
              </motion.div>
            ) : (
              sessions.map((session) => (
                <motion.div
                  key={session.id}
                  className={`session-item ${currentSessionId === session.id ? 'active' : ''}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  {editingId === session.id ? (
                    <div className="session-edit">
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveEdit(session.id);
                          if (e.key === 'Escape') handleCancelEdit();
                        }}
                        autoFocus
                      />
                      <div className="edit-actions">
                        <button onClick={() => handleSaveEdit(session.id)} className="save-btn">
                          <FiCheck />
                        </button>
                        <button onClick={handleCancelEdit} className="cancel-btn">
                          <FiX />
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div 
                      className="session-content"
                      onClick={() => onSelectSession(session.id)}
                    >
                      <div className="session-info">
                        <h3>{session.title}</h3>
                        <span className="session-date">{formatDate(session.updated_at)}</span>
                      </div>
                      <div className="session-actions">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStartEdit(session);
                          }}
                          className="edit-btn"
                          title="Rename"
                        >
                          <FiEdit2 />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (confirm('Delete this chat?')) {
                              onDeleteSession(session.id);
                            }
                          }}
                          className="delete-btn"
                          title="Delete"
                        >
                          <FiTrash2 />
                        </button>
                      </div>
                    </div>
                  )}
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  );
}
