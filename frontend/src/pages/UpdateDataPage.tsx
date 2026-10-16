import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { RefreshCw, ArrowLeft, Globe, Layers, Upload, Clock, CheckCircle2, AlertCircle } from 'lucide-react';

const UpdateDataPage: React.FC = () => {
  const [status, setStatus] = useState<string>('idle');
  const [progress, setProgress] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [knowledgeStats, setKnowledgeStats] = useState<{ document_count: number; chunk_count: number; last_updated: string | null }>({
    document_count: 0,
    chunk_count: 0,
    last_updated: null
  });

  // Custom upload state
  const [uploadTitle, setUploadTitle] = useState<string>('');
  const [uploadContent, setUploadContent] = useState<string>('');
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);

  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8002';

  const fetchKnowledgeStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/knowledge/status`);
      setKnowledgeStats(response.data);
      if (response.data.status) {
        setStatus(response.data.status);
      }
    } catch (err) {
      console.error('Error fetching knowledge status:', err);
    }
  };

  const startCrawl = async () => {
    setStatus('crawling');
    setProgress('Initiating KPGU web crawler...');
    setError(null);
    try {
      await axios.post(`${API_URL}/api/knowledge/crawl`);
    } catch (err) {
      setStatus('failed');
      setError('Failed to initiate website crawling');
    }
  };

  const startRebuild = async () => {
    setStatus('rebuilding');
    setProgress('Rebuilding FAISS index from stored chunks...');
    setError(null);
    try {
      await axios.post(`${API_URL}/api/knowledge/rebuild`);
    } catch (err) {
      setStatus('failed');
      setError('Failed to rebuild knowledge base');
    }
  };

  const handleCustomUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadTitle.trim() || !uploadContent.trim()) return;

    try {
      setUploadMsg('Uploading document...');
      await axios.post(`${API_URL}/api/knowledge/upload`, {
        title: uploadTitle,
        content: uploadContent,
        url: `https://www.kpgu.ac.in/custom-doc/${Date.now()}`
      });
      setUploadMsg('Document uploaded successfully! Knowledge base is updating.');
      setUploadTitle('');
      setUploadContent('');
      fetchKnowledgeStatus();
    } catch (err) {
      setUploadMsg('Failed to upload document');
    }
  };

  useEffect(() => {
    if (['crawling', 'processing', 'embedding', 'rebuilding'].includes(status)) {
      const interval = setInterval(fetchKnowledgeStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [status]);

  useEffect(() => {
    fetchKnowledgeStatus();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-4 md:p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700">
              <RefreshCw className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Knowledge Base Management</h1>
              <p className="text-xs md:text-sm text-slate-500">Rebuild vector index or crawl fresh university information</p>
            </div>
          </div>

          <button
            onClick={() => window.location.href = '/'}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white flex items-center space-x-2 text-xs font-semibold shadow-xs transition-all self-start md:self-auto"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Chat</span>
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="bg-white border border-slate-200 p-5 rounded-2xl flex items-center space-x-4 shadow-xs">
            <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shrink-0">
              <Globe className="w-6 h-6" />
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-900">{knowledgeStats.document_count}</div>
              <div className="text-xs text-slate-500 font-medium">Crawled Pages</div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 p-5 rounded-2xl flex items-center space-x-4 shadow-xs">
            <div className="w-12 h-12 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shrink-0">
              <Layers className="w-6 h-6" />
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-900">{knowledgeStats.chunk_count}</div>
              <div className="text-xs text-slate-500 font-medium">Vector Chunks</div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 p-5 rounded-2xl flex items-center space-x-4 shadow-xs">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 shrink-0">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-900 truncate max-w-[160px]">
                {knowledgeStats.last_updated ? new Date(knowledgeStats.last_updated).toLocaleDateString() : 'Active'}
              </div>
              <div className="text-xs text-slate-500 font-medium">Last Sync Date</div>
            </div>
          </div>
        </div>

        {/* Actions & Custom Upload */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Automatic Sync Actions */}
          <div className="bg-white border border-slate-200 p-6 rounded-2xl space-y-4 shadow-xs">
            <h2 className="text-base font-bold text-slate-900">Automated Pipeline</h2>
            <p className="text-xs text-slate-500 leading-relaxed font-normal">
              Trigger headless web crawler to extract information from KPGU website and update vector store.
            </p>

            <div className="space-y-3 pt-2">
              <button
                onClick={startCrawl}
                disabled={['crawling', 'processing', 'embedding', 'rebuilding'].includes(status)}
                className="w-full py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold text-xs flex items-center justify-center space-x-2 shadow-xs transition-all"
              >
                <Globe className="w-4 h-4" />
                <span>{status === 'crawling' ? 'Crawling KPGU Site...' : 'Crawl KPGU Website'}</span>
              </button>

              <button
                onClick={startRebuild}
                disabled={['crawling', 'processing', 'embedding', 'rebuilding'].includes(status)}
                className="w-full py-3 px-4 rounded-xl bg-white border border-slate-300 hover:bg-slate-50 disabled:opacity-50 text-slate-700 font-semibold text-xs flex items-center justify-center space-x-2 transition-all shadow-xs"
              >
                <RefreshCw className="w-4 h-4 text-emerald-600" />
                <span>{status === 'rebuilding' ? 'Rebuilding Index...' : 'Rebuild FAISS Vector Store'}</span>
              </button>
            </div>

            {progress && ['crawling', 'rebuilding'].includes(status) && (
              <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-blue-700 text-xs flex items-center space-x-2 font-medium">
                <RefreshCw className="w-4 h-4 shrink-0 text-blue-600 animate-spin" />
                <span>{progress}</span>
              </div>
            )}

            {error && (
              <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2 font-medium">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
                <span>{error}</span>
              </div>
            )}

            {status === 'completed' && (
              <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs flex items-center space-x-2 font-medium">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                <span>Knowledge base update completed successfully!</span>
              </div>
            )}
          </div>

          {/* Manual Document Ingestion */}
          <div className="bg-white border border-slate-200 p-6 rounded-2xl space-y-4 shadow-xs">
            <h2 className="text-base font-bold text-slate-900">Manual Document Upload</h2>
            <p className="text-xs text-slate-500 leading-relaxed font-normal">
              Add official university circulars, guidelines, or notice content directly into the vector database.
            </p>

            <form onSubmit={handleCustomUpload} className="space-y-3 pt-1">
              <input
                type="text"
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                placeholder="Document Title (e.g. Admission Guidelines 2026)"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 text-xs font-medium"
              />
              <textarea
                value={uploadContent}
                onChange={(e) => setUploadContent(e.target.value)}
                placeholder="Paste document body text here..."
                rows={4}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 text-xs font-medium resize-none"
              />
              <button
                type="submit"
                disabled={!uploadTitle.trim() || !uploadContent.trim()}
                className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-semibold text-xs flex items-center justify-center space-x-2 shadow-xs transition-all"
              >
                <Upload className="w-4 h-4" />
                <span>Upload &amp; Index Document</span>
              </button>
            </form>

            {uploadMsg && (
              <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-blue-700 text-xs font-medium">
                {uploadMsg}
              </div>
            )}
          </div>
        </div>

        {/* Developer Footer Credit */}
        <div className="pt-4 text-center flex flex-col sm:flex-row items-center justify-center space-y-1 sm:space-y-0 sm:space-x-2 text-xs text-slate-500">
          <span className="flex items-center space-x-1 font-medium">
            <span>Made with</span>
            <span className="text-rose-500 text-sm leading-none animate-pulse">❤️</span>
            <span>by</span>
            <strong className="font-semibold text-slate-800 hover:text-blue-600 transition-colors">
              Nisarg Shah &amp; Harsh Shah
            </strong>
          </span>
          <span className="hidden sm:inline text-slate-400">·</span>
          <span className="text-[11px] text-blue-700 font-semibold tracking-wide bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
            KPGU Students
          </span>
        </div>
      </div>
    </div>
  );
};

export default UpdateDataPage;