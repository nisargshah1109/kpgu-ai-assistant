import React from 'react';
import { Info, ArrowLeft, Bot, ShieldCheck, Cpu, ExternalLink } from 'lucide-react';

const AboutPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-4 md:p-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 pb-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-purple-50 border border-purple-200 flex items-center justify-center text-purple-700">
              <Info className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">About KPGU AI Assistant</h1>
              <p className="text-xs md:text-sm text-slate-500">System Architecture, AI Engine &amp; Technical Specifications</p>
            </div>
          </div>

          <button
            onClick={() => window.location.href = '/'}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white flex items-center space-x-2 text-xs font-semibold shadow-xs transition-all"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Chat</span>
          </button>
        </div>

        {/* Info Cards */}
        <div className="bg-white border border-slate-200 p-6 md:p-8 rounded-3xl space-y-8 shadow-xs">
          <div className="flex items-center space-x-4 pb-6 border-b border-slate-100">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-700 to-sky-500 flex items-center justify-center shadow-xs text-white shrink-0">
              <Bot className="w-7 h-7 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">KPGU AI Assistant v2.0</h2>
              <p className="text-xs text-blue-700 font-semibold mt-0.5">Drs. Kiran and Pallavi Patel Global University Assistant</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="kpgu-card p-6 rounded-2xl space-y-3">
              <div className="flex items-center space-x-2 text-blue-700 font-semibold text-xs">
                <GlobeIcon className="w-4 h-4" />
                <span>Knowledge Source</span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Extracted &amp; indexed directly from official KPGU website pages:
              </p>
              <a 
                href="https://www.kpgu.ac.in/" 
                target="_blank" 
                rel="noreferrer"
                className="inline-flex items-center space-x-1.5 text-blue-600 hover:underline text-xs font-semibold"
              >
                <span>https://www.kpgu.ac.in/</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>

            <div className="kpgu-card p-6 rounded-2xl space-y-3">
              <div className="flex items-center space-x-2 text-purple-700 font-semibold text-xs">
                <Cpu className="w-4 h-4" />
                <span>AI &amp; RAG Technology</span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Powered by Google Gemini 1.5 Flash RAG architecture with FAISS vector similarity retrieval and sentence-transformers embeddings (<code className="bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 font-medium">all-MiniLM-L6-v2</code>).
              </p>
            </div>

            <div className="kpgu-card p-6 rounded-2xl space-y-3">
              <div className="flex items-center space-x-2 text-emerald-700 font-semibold text-xs">
                <ShieldCheck className="w-4 h-4" />
                <span>Privacy &amp; Security</span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                All conversation history is persisted securely in local SQLite storage. No personal information is stored or shared.
              </p>
            </div>

            <div className="kpgu-card p-6 rounded-2xl space-y-3">
              <div className="flex items-center space-x-2 text-amber-700 font-semibold text-xs">
                <Bot className="w-4 h-4" />
                <span>Accuracy &amp; Integrity</span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Strict Query Gating &amp; Relevance Thresholds prevent hallucinations by outputting <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">Not in data set.</code> for out-of-scope requests.
              </p>
            </div>
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

const GlobeIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
  </svg>
);

export default AboutPage;