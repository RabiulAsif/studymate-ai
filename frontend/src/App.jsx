import { useState, useEffect, useRef } from "react";
import "./App.css";
import { v4 as uuidv4 } from "uuid";

function App() {
  // User state
  const [currentUserId, setCurrentUserId] = useState(null);

  // Chat state
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([]);
  const [loading, setLoading] = useState(false);

  // Session state
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [isFirstMessage, setIsFirstMessage] = useState(true);

  // PDF state
  const [pdfs, setPdfs] = useState([]);
  const [showPdfUpload, setShowPdfUpload] = useState(false);

  // Ref for textarea auto-focus
  const textareaRef = useRef(null);

  // API URL
  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

  // ========== INITIALIZE USER ID ON MOUNT ==========
  useEffect(() => {
    initializeUser();
  }, []);

  // ========== INITIALIZE USER AND LOAD LAST SESSION ==========
  const initializeUser = async () => {
    // Create/load user ID
    let userId = localStorage.getItem("studymate_user_id");
    if (!userId) {
      userId = uuidv4();
      localStorage.setItem("studymate_user_id", userId);
      console.log("✅ New user ID created:", userId);
    } else {
      console.log("✅ User ID loaded:", userId);
    }

    setCurrentUserId(userId);

    // Auto-load last session on page refresh
    try {
      const res = await fetch(`${API_URL}/last-session?user_id=${userId}`);
      const data = await res.json();

      if (data.session_id) {
        console.log("✅ Found last session:", data.session_id);
        setCurrentSessionId(data.session_id);
        await loadChatForSession(data.session_id, userId);
        setIsFirstMessage(false);
      } else {
        console.log("No previous session found");
        setIsFirstMessage(true);
      }
    } catch (error) {
      console.error("Error loading last session:", error);
      setIsFirstMessage(true);
    }

    // Load sessions list
    await loadSessions(userId);
  };

  // ========== LOAD SESSIONS FOR CURRENT USER ==========
  const loadSessions = async (userId) => {
    if (!userId) return;

    setLoadingHistory(true);
    try {
      const res = await fetch(`${API_URL}/sessions?user_id=${userId}`);
      const data = await res.json();

      if (data.sessions && data.sessions.length > 0) {
        const sessions = data.sessions.map((session) => ({
          id: session.session_id,
          name: session.user_name || "Chat",
          createdAt: session.created_at,
        }));
        setChatHistory(sessions);
      } else {
        setChatHistory([]);
      }
    } catch (error) {
      console.error("Error loading sessions:", error);
      setChatHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  // ========== LOAD CHAT FOR A SPECIFIC SESSION ==========
  const loadChatForSession = async (sessionId, userId) => {
    try {
      const res = await fetch(
        `${API_URL}/session/${sessionId}/history?user_id=${userId}`
      );
      const data = await res.json();

      const chatArray = [];
      if (data.history && data.history.length > 0) {
        for (let i = 0; i < data.history.length; i += 2) {
          if (data.history[i]) {
            chatArray.push({
              role: "user",
              text: data.history[i].content,
            });
          }
          if (data.history[i + 1]) {
            chatArray.push({
              role: "bot",
              text: data.history[i + 1].content,
            });
          }
        }
      }

      setChat(chatArray);
      return true;
    } catch (error) {
      console.error("Error loading chat:", error);
      return false;
    }
  };

  // ========== CREATE NEW CHAT SESSION ==========
  const newChat = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/new-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: currentUserId }),
      });

      const data = await res.json();
      const newSessionId = data.session_id;

      setChat([]);
      setCurrentSessionId(newSessionId);
      setMessage("");
      setPdfs([]);
      setIsFirstMessage(true);

      // Auto-focus textarea
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
        }
      }, 100);

      await loadSessions(currentUserId);
    } catch (error) {
      console.error("Error creating new session:", error);
      alert("Error creating new chat");
    } finally {
      setLoading(false);
    }
  };

  // ========== LOAD PREVIOUS CHAT HISTORY ==========
  const loadChat = async (sessionId) => {
    setLoadingHistory(true);
    try {
      const success = await loadChatForSession(sessionId, currentUserId);
      if (success) {
        setCurrentSessionId(sessionId);
        setMessage("");
        setIsFirstMessage(false);
        await loadSessionPdfs(sessionId);

        // Auto-focus textarea
        setTimeout(() => {
          if (textareaRef.current) {
            textareaRef.current.focus();
          }
        }, 100);
      }
    } catch (error) {
      console.error("Error loading chat:", error);
      alert("Error loading chat history");
    } finally {
      setLoadingHistory(false);
    }
  };

  // ========== DELETE CHAT SESSION ==========
  const deleteChat = async (sessionId, e) => {
    e.stopPropagation(); // Prevent loading the chat when clicking delete

    // Confirm delete
    if (!window.confirm("Are you sure you want to delete this chat?")) {
      return;
    }

    try {
      const res = await fetch(
        `${API_URL}/session/${sessionId}?user_id=${currentUserId}`,
        {
          method: "DELETE",
        }
      );

      const data = await res.json();

      if (data.status === "success") {
        // Remove from sidebar
        setChatHistory(chatHistory.filter((chat) => chat.id !== sessionId));

        // Clear chat if it's the current one
        if (currentSessionId === sessionId) {
          setChat([]);
          setCurrentSessionId(null);
          setMessage("");
          setPdfs([]);
        }

        console.log("✅ Chat deleted successfully");
      } else {
        alert("Error deleting chat: " + data.message);
      }
    } catch (error) {
      console.error("Error deleting chat:", error);
      alert("Error deleting chat");
    }
  };

  // ========== SEND MESSAGE TO AI ==========
  const sendMessage = async () => {
    if (!message.trim() || !currentUserId) return;

    setLoading(true);

    const sessionId = currentSessionId || (await createNewSession());

    const history = chat.map((c) => ({
      role: c.role === "user" ? "user" : "assistant",
      content: c.text,
    }));

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: message,
          user_id: currentUserId,
          session_id: sessionId,
          history: history,
          is_first_message: isFirstMessage,
        }),
      });

      const data = await res.json();

      const newChat = [
        ...chat,
        { role: "user", text: message },
        { role: "bot", text: data.reply },
      ];

      setChat(newChat);
      setCurrentSessionId(data.session_id);
      setMessage("");
      setIsFirstMessage(false);

      // Auto-focus textarea after sending
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
        }
      }, 100);

      await loadSessions(currentUserId);
    } catch (error) {
      console.error("Error:", error);
      setChat([
        ...chat,
        { role: "user", text: message },
        { role: "bot", text: "❌ Error: Could not get response from server" },
      ]);

      // Auto-focus textarea after error
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
        }
      }, 100);
    } finally {
      setLoading(false);
    }
  };

  // ========== CREATE NEW SESSION HELPER ==========
  const createNewSession = async () => {
    try {
      const res = await fetch(`${API_URL}/new-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: currentUserId }),
      });

      const data = await res.json();
      setIsFirstMessage(true);
      return data.session_id;
    } catch (error) {
      console.error("Error creating session:", error);
      return null;
    }
  };

  // ========== HANDLE KEYBOARD (ENTER TO SEND) ==========
  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // ========== LOAD SESSION PDFS ==========
  const loadSessionPdfs = async (sessionId) => {
    try {
      const res = await fetch(
        `${API_URL}/session/${sessionId}/pdfs?user_id=${currentUserId}`
      );
      const data = await res.json();

      if (data.pdfs && data.pdfs.length > 0) {
        setPdfs(data.pdfs.map((pdf) => pdf.filename));
      } else {
        setPdfs([]);
      }
    } catch (error) {
      console.error("Error loading PDFs:", error);
      setPdfs([]);
    }
  };

  // ========== UPLOAD PDF ==========
  const handlePdfUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("user_id", currentUserId);
    if (currentSessionId) {
      formData.append("session_id", currentSessionId);
    }

    try {
      const res = await fetch(`${API_URL}/upload-pdf`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (data.success) {
        setPdfs([...pdfs, data.filename]);
        setChat([
          ...chat,
          {
            role: "bot",
            text: `✅ PDF "${data.filename}" uploaded successfully! (${data.pages} pages)\n\nI can now answer questions based on this document!`,
          },
        ]);
      } else {
        setChat([...chat, { role: "bot", text: `❌ Error: ${data.message}` }]);
      }
    } catch (error) {
      console.error("Error uploading PDF:", error);
      setChat([...chat, { role: "bot", text: "❌ Error uploading PDF" }]);
    }

    setShowPdfUpload(false);
  };

  // ========== DELETE PDF ==========
  const deletePdf = async (filename) => {
    try {
      const res = await fetch(
        `${API_URL}/session/${currentSessionId}/pdfs/${filename}?user_id=${currentUserId}`,
        { method: "DELETE" }
      );

      const data = await res.json();

      if (data.success) {
        setPdfs(pdfs.filter((pdf) => pdf !== filename));
      }
    } catch (error) {
      console.error("Error deleting PDF:", error);
    }
  };

  // ========== RENDER ==========
  return (
    <>
      <div className="app-container">
        {/* ========== SIDEBAR ========== */}
        <aside className="sidebar">
          <div className="sidebar-header">
            <h1>StudyMate AI</h1>
            <p style={{ fontSize: "11px", color: "rgba(255,255,255,0.4)" }}>
              Your private session
            </p>
          </div>

          <button className="new-chat-btn" onClick={newChat} disabled={loading}>
            + New Chat
          </button>

          {/* Chat History */}
          <div className="chat-history">
            {loadingHistory ? (
              <p style={{ textAlign: "center", color: "rgba(255,255,255,0.5)" }}>
                Loading chats...
              </p>
            ) : chatHistory.length > 0 ? (
              chatHistory.map((chatItem) => (
                <div
                  key={chatItem.id}
                  className={`chat-item ${
                    currentSessionId === chatItem.id ? "active" : ""
                  }`}
                  onClick={() => loadChat(chatItem.id)}
                  title={chatItem.name}
                >
                  <span>{chatItem.name}</span>
                  <button
                    className="delete-chat-btn"
                    onClick={(e) => deleteChat(chatItem.id, e)}
                    title="Delete chat"
                  >
                    ✕
                  </button>
                </div>
              ))
            ) : (
              <p style={{ textAlign: "center", color: "rgba(255,255,255,0.4)" }}>
                No chats yet
              </p>
            )}
          </div>

          {/* PDF Section */}
          <div className="pdf-section">
            <h3>📄 Uploaded PDFs</h3>
            <button
              className="upload-pdf-btn"
              onClick={() => setShowPdfUpload(!showPdfUpload)}
            >
              + Upload PDF
            </button>

            {showPdfUpload && (
              <div className="pdf-upload-box">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handlePdfUpload}
                  className="file-input"
                />
              </div>
            )}

            <div className="pdf-list">
              {pdfs.map((pdf, index) => (
                <div key={index} className="pdf-item">
                  <span>{pdf}</span>
                  <button
                    className="delete-pdf-btn"
                    onClick={() => deletePdf(pdf)}
                    title="Delete PDF"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* ========== MAIN CHAT AREA ========== */}
        <main className="main-content">
          <div className="chat-header">
            <p>👋 Hello! I'm your AI Study Assistant.</p>
            <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.5)" }}>
              💡 Your chats are private and only visible to you
            </p>
            {pdfs.length > 0 && (
              <p className="pdf-info">📚 {pdfs.length} PDF(s) uploaded</p>
            )}
          </div>

          <div className="chat-box">
            {chat.length === 0 && (
              <div className="welcome-section">
                <h2>Welcome to StudyMate AI</h2>
                <p>Ask me anything about your studies!</p>
                <p className="subtitle">
                  Upload PDFs to ask questions about their content
                </p>
              </div>
            )}

            {chat.map((c, i) => (
              <div key={i} className={`message ${c.role}`}>
                <div className="message-content">
                  <p>{c.text}</p>
                </div>
              </div>
            ))}

            {loading && (
              <div className="message bot">
                <div className="message-content">
                  <p className="typing">⏳ Thinking...</p>
                </div>
              </div>
            )}
          </div>

          <div className="input-container">
            <div className="input-box">
              <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your study question..."
                disabled={loading || !currentUserId}
                rows="1"
                autoFocus
              />
              <button
                className="send-btn"
                onClick={sendMessage}
                disabled={loading || !currentUserId}
              >
                {loading ? "Sending..." : "Send"}
              </button>
            </div>
          </div>
        </main>
      </div>

      {/* ========== FOOTER ========== */}
      <div className="app-footer">
        Built by{" "}
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          title="GitHub Profile"
        >
          MD. Rabiul Islam Asif
        </a>
      </div>
    </>
  );
}

export default App;