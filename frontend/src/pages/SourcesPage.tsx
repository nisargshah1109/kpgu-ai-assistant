import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Database, ArrowLeft, ExternalLink, Search, RefreshCw, CheckCircle2 } from 'lucide-react';

interface SourceItem {
  id: number;
  title: string;
  url: string;
  last_updated: string;
  status: string;
}

const SourcesPage: React.FC = () => {
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8002';

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_URL}/api/sources`);
      setSources(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch indexed sources from server');
      setLoading(false);
    }
  };

  const filteredSources = sources.filter(s =>
    s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.url.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-4 md:p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Navigation & Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Indexed Knowledge Sources</h1>
              <p className="text-xs md:text-sm text-slate-500">Website pages and documents stored in FAISS vector database</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={fetchSources}
              className="px-3.5 py-2 rounded-xl bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 flex items-center space-x-2 text-xs font-semibold shadow-xs transition-all"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-600' : ''}`} />
              <span>Refresh</span>
            </button>
            <button
              onClick={() => window.location.href = '/'}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white flex items-center space-x-2 text-xs font-semibold shadow-xs transition-all"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Chat</span>
            </button>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="relative max-w-md">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter sources by title or URL..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white border border-slate-300 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-600/20 text-xs font-medium"
          />
        </div>

        {/* Data Table */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-red-600 text-xs font-medium">
            {error}
          </div>
        ) : filteredSources.length === 0 ? (
          <div className="kpgu-panel rounded-2xl p-12 text-center text-slate-500 text-xs font-medium">
            No indexed sources found matching your query.
          </div>
        ) : (
          <div className="bg-white rounded-2xl overflow-hidden border border-slate-200 shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-200 font-semibold">
                  <tr>
                    <th className="px-6 py-4 font-semibold">Title</th>
                    <th className="px-6 py-4 font-semibold">Source URL</th>
                    <th className="px-6 py-4 font-semibold">Last Synced</th>
                    <th className="px-6 py-4 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredSources.map(source => (
                    <tr key={source.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4 font-semibold text-slate-900 max-w-xs truncate">
                        {source.title}
                      </td>
                      <td className="px-6 py-4 text-blue-600 max-w-md truncate font-medium">
                        <a 
                          href={source.url} 
                          target="_blank" 
                          rel="noreferrer"
                          className="hover:underline flex items-center space-x-1.5"
                        >
                          <span className="truncate">{source.url}</span>
                          <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                        </a>
                      </td>
                      <td className="px-6 py-4 text-slate-500 font-medium">
                        {source.last_updated}
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>{source.status}</span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

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

export default SourcesPage;