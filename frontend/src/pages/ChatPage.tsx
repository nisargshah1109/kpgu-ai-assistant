import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  MessageSquare, 
  Plus, 
  Trash2, 
  Database, 
  RefreshCw, 
  Info, 
  Send, 
  GraduationCap, 
  BookOpen, 
  Home, 
  Briefcase,
  Bot,
  User,
  Copy,
  Check,
  Menu,
  X,
  ExternalLink,
  ShieldCheck,
  FileText,
  AlertCircle,
  Download,
  HelpCircle
} from 'lucide-react';

interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

interface SourceItem {
  title: string;
  url: string;
  last_updated?: string;
}

interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  sources?: SourceItem[];
  data_found?: boolean;
  is_ambiguous?: boolean;
  clarification_options?: string[];
  pdf_export_url?: string;
}

const ChatPage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [copiedMessageId, setCopiedMessageId] = useState<number | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [serverError, setServerError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8002';

  const suggestedQuestions = [
    { title: "UG Admissions Process", desc: "Eligibility, application deadline & ACPC criteria", icon: GraduationCap, query: "What is the admission procedure for undergraduate courses at KPGU?" },
    { title: "Diploma to Degree (D2D)", desc: "Direct 2nd-year B.Tech & B.Pharm lateral entry", icon: BookOpen, query: "Is Diploma to Degree (D2D) lateral entry available for engineering?" },
    { title: "Computer Science Fees", desc: "Tuition fee structure & entrance test requirements", icon: Briefcase, query: "What are the tuition fees for B.Tech Computer Engineering?" },
    { title: "Hostel & Housing", desc: "Boys & Girls AC/Non-AC rooms, Wi-Fi & mess", icon: Home, query: "What hostel facilities and accommodation options are available on campus?" }
  ];

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConversations = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/conversations`);
      setConversations(response.data);
      if (currentConversationId === null && response.data.length > 0) {
        setCurrentConversationId(response.data[0].id);
        fetchMessages(response.data[0].id);
      }
    } catch (error) {
      console.error('Error fetching conversations:', error);
    }
  };

  const fetchMessages = async (conversationId: number) => {
    try {
      const response = await axios.get(`${API_URL}/api/conversations/${conversationId}/messages`);
      setMessages(response.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const handleNewChat = async () => {
    try {
      const response = await axios.post(`${API_URL}/api/conversations`, {});
      const newConv = response.data;
      setConversations(prev => [newConv, ...prev]);
      setCurrentConversationId(newConv.id);
      setMessages([]);
      setInput('');
      setServerError(null);
    } catch (error) {
      console.error('Error creating new conversation:', error);
      setServerError(`Unable to connect to backend server at ${API_URL}. Please verify Uvicorn server is running.`);
    }
  };

  const handleSelectConversation = (id: number) => {
    setCurrentConversationId(id);
    fetchMessages(id);
  };

  const handleDeleteConversation = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    try {
      await axios.delete(`${API_URL}/api/conversations/${id}`);
      setConversations(prev => prev.filter(c => c.id !== id));
      if (currentConversationId === id) {
        const remaining = conversations.filter(c => c.id !== id);
        if (remaining.length > 0) {
          setCurrentConversationId(remaining[0].id);
          fetchMessages(remaining[0].id);
        } else {
          setCurrentConversationId(null);
          setMessages([]);
        }
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const messageContent = textToSend || input;
    if (!messageContent.trim() || loading) return;

    setServerError(null);
    let convId = currentConversationId;
    
    if (!convId) {
      try {
        const response = await axios.post(`${API_URL}/api/conversations`, {});
        const newConv = response.data;
        setConversations(prev => [newConv, ...prev]);
        convId = newConv.id;
        setCurrentConversationId(convId);
      } catch (err: any) {
        console.error('Failed to create conversation:', err);
        setServerError(`Unable to connect to backend server at ${API_URL}. Please verify your Python Uvicorn server is running.`);
        return;
      }
    }
    if (!convId) return;
    const activeConvId = convId as number;

    setLoading(true);
    setInput('');

    const tempUserMsg: Message = {
      id: Date.now(),
      conversation_id: activeConvId,
      role: 'user',
      content: messageContent,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const response = await axios.post(`${API_URL}/api/chat`, {
        conversation_id: activeConvId,
        message: messageContent
      });

      const assistantMsg: Message = {
        id: response.data.message_id || Date.now() + 1,
        conversation_id: activeConvId,
        role: 'assistant',
        content: response.data.answer,
        created_at: new Date().toISOString(),
        sources: response.data.sources || [],
        data_found: response.data.data_found !== false,
        is_ambiguous: response.data.is_ambiguous || false,
        clarification_options: response.data.clarification_options || [],
        pdf_export_url: response.data.pdf_export_url
      };

      setMessages(prev => [...prev, assistantMsg]);
      fetchConversations();
    } catch (error: any) {
      console.error('Error sending message:', error);
      const errorMsg: Message = {
        id: Date.now() + 1,
        conversation_id: activeConvId,
        role: 'assistant',
        content: "The assistant is temporarily unavailable. Please verify that your Python FastAPI server is running.",
        created_at: new Date().toISOString(),
        data_found: false
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyMessage = (id: number, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedMessageId(id);
    setTimeout(() => setCopiedMessageId(null), 2000);
  };

  const handleDownloadChatPDF = () => {
    if (!currentConversationId) return;
    window.open(`${API_URL}/api/conversations/${currentConversationId}/export-pdf`, '_blank');
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans overflow-hidden">
      {/* Mobile Drawer Backdrop */}
      {sidebarOpen && (
        <div 
          onClick={() => setSidebarOpen(false)}
          className="md:hidden fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-20"
        />
      )}

      {/* Sidebar Navigation */}
      <aside 
        className={`fixed md:static inset-y-0 left-0 z-30 w-72 bg-white border-r border-slate-200 flex flex-col transition-all duration-300 transform ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0 md:w-72'
        }`}
      >
        {/* Brand Header */}
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-blue-700 flex items-center justify-center text-white shadow-sm font-bold text-lg">
              K
            </div>
            <div>
              <h1 className="font-bold text-slate-900 text-sm tracking-tight">KPGU AI Assistant</h1>
              <p className="text-[11px] text-blue-600 font-medium">General Knowledge Engine</p>
            </div>
          </div>
          <button 
            onClick={() => setSidebarOpen(false)}
            className="md:hidden p-1.5 rounded-lg text-slate-500 hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <button
            onClick={handleNewChat}
            className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm flex items-center justify-center space-x-2 shadow-sm transition-all duration-200"
          >
            <Plus className="w-4 h-4" />
            <span>New Conversation</span>
          </button>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto px-3 space-y-1">
          <div className="px-3 py-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            History
          </div>
          {conversations.length === 0 ? (
            <div className="px-3 py-4 text-center text-xs text-slate-400">
              No previous chats
            </div>
          ) : (
            conversations.map(conv => (
              <div
                key={conv.id}
                onClick={() => handleSelectConversation(conv.id)}
                className={`group flex items-center justify-between px-3 py-2.5 rounded-xl cursor-pointer text-xs font-medium transition-all ${
                  currentConversationId === conv.id
                    ? 'bg-blue-50 text-blue-700 font-semibold border border-blue-200/60'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                <div className="flex items-center space-x-2.5 min-w-0">
                  <MessageSquare className={`w-4 h-4 shrink-0 ${currentConversationId === conv.id ? 'text-blue-600' : 'text-slate-400'}`} />
                  <span className="truncate">{conv.title || 'New Conversation'}</span>
                </div>
                <button
                  onClick={(e) => handleDeleteConversation(e, conv.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-red-50 text-slate-400 hover:text-red-600 transition-all"
                  title="Delete chat"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))
          )}
        </div>

        {/* Page Nav Links */}
        <div className="p-3 border-t border-slate-200 space-y-1">
          <a
            href="/sources"
            className="flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all"
          >
            <Database className="w-4 h-4 text-slate-400" />
            <span>Indexed Sources</span>
          </a>
          <a
            href="/update-data"
            className="flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all"
          >
            <RefreshCw className="w-4 h-4 text-slate-400" />
            <span>Data Sync Portal</span>
          </a>
          <a
            href="/about"
            className="flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all"
          >
            <Info className="w-4 h-4 text-slate-400" />
            <span>About &amp; Tech Specs</span>
          </a>
        </div>

        {/* Developer Footer Credit */}
        <div className="p-3 border-t border-slate-200 text-center bg-slate-50">
          <div className="text-[11px] text-slate-500 font-medium leading-relaxed">
            <span>Made with </span>
            <span className="text-rose-500 font-bold animate-pulse">❤️</span>
            <span> by </span>
            <strong className="text-slate-800 font-semibold">Nisarg Shah &amp; Harsh Shah</strong>
          </div>
          <div className="mt-0.5 text-[10px] text-blue-600 font-semibold uppercase tracking-wider">
            KPGU Students
          </div>
        </div>
      </aside>

      {/* Main Chat Interface */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50">
        {/* Top Navbar Header */}
        <header className="h-16 px-4 md:px-6 bg-white border-b border-slate-200 flex items-center justify-between shrink-0 shadow-xs">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="md:hidden p-2 rounded-xl text-slate-600 hover:bg-slate-100"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-xs font-semibold text-slate-800">
                Universal KPGU Knowledge Base
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs text-slate-500 font-medium">
            {/* Download Whole Chat PDF Button */}
            {currentConversationId && (
              <button
                onClick={handleDownloadChatPDF}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-blue-50 text-slate-700 hover:text-blue-700 border border-slate-200 text-xs font-semibold transition-all shadow-xs"
                title="Export complete conversation thread to PDF / Document"
              >
                <Download className="w-3.5 h-3.5 text-blue-600" />
                <span>Download Chat</span>
              </button>
            )}

            <span className="hidden sm:inline-block px-2.5 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 font-semibold text-[11px]">
              Universal RAG Engine
            </span>
          </div>
        </header>

        {/* Server Alert Banner */}
        {serverError && (
          <div className="bg-amber-50 border-b border-amber-200 p-3 text-xs text-amber-800 flex items-center justify-between px-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>{serverError}</span>
            </div>
            <button onClick={() => setServerError(null)} className="text-amber-600 hover:underline text-xs font-semibold">
              Dismiss
            </button>
          </div>
        )}

        {/* Chat Area Scroll Container */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
          {messages.length === 0 ? (
            /* Hero Welcome Screen */
            <div className="max-w-3xl mx-auto py-8 text-center space-y-8 animate-fade-in">
              <div className="space-y-3">
                <div className="w-16 h-16 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700 mx-auto shadow-xs">
                  <GraduationCap className="w-8 h-8" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
                  KPGU AI Assistant
                </h2>
                <p className="text-xs md:text-sm text-slate-500 max-w-lg mx-auto leading-relaxed">
                  General University Knowledge Assistant for Drs. Kiran &amp; Pallavi Patel Global University, Vadodara. Answers any query available in the KPGU dataset.
                </p>
              </div>

              {/* Verified Dataset Notice Badge */}
              <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-slate-600 text-xs font-medium">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Knowledge scope is determined dynamically by the dataset</span>
              </div>

              {/* Suggested Query Cards Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left max-w-2xl mx-auto pt-2">
                {suggestedQuestions.map((sq, idx) => {
                  const Icon = sq.icon;
                  return (
                    <div
                      key={idx}
                      onClick={() => handleSendMessage(sq.query)}
                      className="kpgu-card p-4 rounded-2xl cursor-pointer group flex flex-col justify-between"
                    >
                      <div className="flex items-center space-x-3 mb-2">
                        <div className="w-8 h-8 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-all">
                          <Icon className="w-4 h-4" />
                        </div>
                        <h3 className="font-semibold text-xs text-slate-800 group-hover:text-blue-600 transition-colors">
                          {sq.title}
                        </h3>
                      </div>
                      <p className="text-[11px] text-slate-500 leading-snug">
                        {sq.desc}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            /* Active Conversation Message List */
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex items-start space-x-3 animate-fade-in ${
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {/* Assistant Avatar */}
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-xl bg-blue-700 flex items-center justify-center text-white shrink-0 shadow-xs mt-1">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  {/* Message Bubble Content */}
                  <div
                    className={`max-w-[85%] rounded-2xl p-4 text-xs md:text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white shadow-xs rounded-tr-none'
                        : 'bg-white border border-slate-200 text-slate-800 shadow-xs rounded-tl-none'
                    }`}
                  >
                    {/* Assistant Response Formatting */}
                    {msg.role === 'assistant' ? (
                      <div className="space-y-3">
                        {/* Out of Dataset Notice Badge */}
                        {msg.content.trim() === "Not in data set." ? (
                          <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 space-y-1">
                            <div className="flex items-center space-x-2 font-semibold text-xs text-amber-800">
                              <AlertCircle className="w-4 h-4 text-amber-600" />
                              <span>Not in data set</span>
                            </div>
                            <p className="text-xs text-amber-700 leading-relaxed">
                              This information is currently not available in the KPGU knowledge base.
                            </p>
                          </div>
                        ) : msg.is_ambiguous ? (
                          /* Ambiguity Clarification Request Card */
                          <div className="p-3.5 rounded-xl bg-blue-50/80 border border-blue-200 text-blue-900 space-y-3">
                            <div className="flex items-center space-x-2 font-semibold text-xs text-blue-800">
                              <HelpCircle className="w-4 h-4 text-blue-600 shrink-0" />
                              <span>Clarification Requested</span>
                            </div>
                            <p className="text-xs text-blue-900 font-medium">
                              {msg.content}
                            </p>
                            {msg.clarification_options && msg.clarification_options.length > 0 && (
                              <div className="flex flex-wrap gap-2 pt-1">
                                {msg.clarification_options.map((opt, oIdx) => (
                                  <button
                                    key={oIdx}
                                    onClick={() => handleSendMessage(opt)}
                                    className="px-3 py-1.5 rounded-lg bg-white border border-blue-300 hover:bg-blue-600 hover:text-white text-blue-700 font-semibold text-xs shadow-2xs transition-all"
                                  >
                                    {opt}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        ) : (
                          /* Normal Factual Answer */
                          <div className="whitespace-pre-wrap font-normal text-slate-800 leading-relaxed space-y-2">
                            {msg.content}
                          </div>
                        )}

                        {/* PDF Download Card if Explicitly Requested */}
                        {msg.pdf_export_url && (
                          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center justify-between">
                            <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-900">
                              <FileText className="w-4 h-4 text-emerald-600" />
                              <span>Requested Document PDF Ready</span>
                            </div>
                            <a
                              href={msg.pdf_export_url}
                              target="_blank"
                              rel="noreferrer"
                              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs shadow-xs transition-all flex items-center space-x-1"
                            >
                              <Download className="w-3.5 h-3.5" />
                              <span>Download PDF</span>
                            </a>
                          </div>
                        )}

                        {/* Verified Sources List */}
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="pt-3 border-t border-slate-100 space-y-1.5">
                            <div className="text-[11px] font-semibold text-slate-500 flex items-center space-x-1.5">
                              <FileText className="w-3.5 h-3.5 text-blue-600" />
                              <span>Verified Sources:</span>
                            </div>
                            <div className="flex flex-wrap gap-1.5 pt-0.5">
                              {msg.sources.map((src, sIdx) => (
                                <a
                                  key={sIdx}
                                  href={src.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center space-x-1 text-[11px] font-medium px-2 py-1 rounded-lg bg-slate-100 hover:bg-blue-50 text-blue-600 border border-slate-200 hover:border-blue-200 transition-all"
                                >
                                  <span>{src.title}</span>
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Message Action Bar */}
                        <div className="pt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100">
                          <span>KPGU Universal Knowledge Base</span>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => handleCopyMessage(msg.id, msg.content)}
                              className="p-1 rounded hover:bg-slate-100 text-slate-500 transition-colors flex items-center space-x-1"
                              title="Copy answer"
                            >
                              {copiedMessageId === msg.id ? (
                                <Check className="w-3.5 h-3.5 text-emerald-600" />
                              ) : (
                                <Copy className="w-3.5 h-3.5" />
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                    ) : (
                      /* User Message */
                      <div className="whitespace-pre-wrap font-medium">
                        {msg.content}
                      </div>
                    )}
                  </div>

                  {/* User Avatar */}
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-xl bg-slate-900 flex items-center justify-center text-white shrink-0 shadow-xs mt-1">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              ))}

              {/* Typing Indicator Loading Animation */}
              {loading && (
                <div className="flex items-start space-x-3 animate-fade-in">
                  <div className="w-8 h-8 rounded-xl bg-blue-700 flex items-center justify-center text-white shrink-0 shadow-xs">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none p-4 shadow-xs flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full bg-blue-600 typing-dot-1"></span>
                    <span className="w-2 h-2 rounded-full bg-blue-600 typing-dot-2"></span>
                    <span className="w-2 h-2 rounded-full bg-blue-600 typing-dot-3"></span>
                    <span className="text-xs font-medium text-slate-500 pl-2">Searching dataset &amp; validating context...</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Bar Form */}
        <div className="p-4 md:p-6 bg-white border-t border-slate-200 shrink-0">
          <div className="max-w-3xl mx-auto">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="relative flex items-center"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="Ask anything (e.g. What is KSET?, B.Tech admission, CSE syllabus, hostel)..."
                className="w-full pl-5 pr-14 py-3.5 rounded-2xl bg-slate-50 border border-slate-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-600/20 text-xs md:text-sm font-medium transition-all"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="absolute right-2 p-2.5 rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 transition-all shadow-xs"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
            <div className="mt-2 text-center text-[11px] text-slate-500 font-medium flex items-center justify-center space-x-2">
              <span>Universal Dataset Knowledge Scope</span>
              <span>&bull;</span>
              <span>Ask for PDF anytime (e.g. <code className="bg-slate-100 px-1 rounded text-slate-700 font-semibold">Give me KSET in PDF</code>)</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ChatPage;