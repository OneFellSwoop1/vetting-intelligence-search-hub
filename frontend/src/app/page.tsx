'use client';

// Main search page for the Vetting Intelligence Search Hub
// This will eventually replace pages/index.js

export default function SearchPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent mb-4">
            Vetting Intelligence Search Hub
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            One search. Total transparency.
          </p>
        </div>

        {/* Search Interface - Placeholder for now */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 border border-gray-100">
          <div className="text-center">
            <p className="text-lg text-gray-600 mb-4">
              🚧 App Router Migration in Progress
            </p>
            <p className="text-sm text-gray-500">
              Enhanced search interface coming soon with shadcn/ui components, TanStack Query, and Zustand state management.
            </p>
            <div className="mt-6">
              <a 
                href="/pages-version"
                className="inline-flex items-center px-6 py-3 bg-primary-500 text-white rounded-lg font-semibold hover:bg-primary-600 transition-colors"
              >
                Use Current Version →
              </a>
            </div>
          </div>
        </div>

        {/* Progress Indicator */}
        <div className="bg-white rounded-xl p-6 border border-gray-100">
          <h3 className="text-lg font-semibold mb-4">Migration Progress</h3>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <span className="text-green-500">✅</span>
              <span>TypeScript & App Router setup</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-green-500">✅</span>
              <span>Tailwind config with brand colors</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-green-500">✅</span>
              <span>Core types and API client</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-yellow-500">🔄</span>
              <span>shadcn/ui components (in progress)</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-gray-400">⏳</span>
              <span>Enhanced search interface</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-gray-400">⏳</span>
              <span>Results dashboard with tabs</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-gray-400">⏳</span>
              <span>Advanced modal with record details</span>
            </div>
          </div>
        </div>

        <footer className="mt-12 text-center text-gray-500 text-sm">
          <p>Vetting Intelligence Search Hub - Government Data Analysis Platform</p>
          <p className="mt-2">Search across NYC, NYS, and Federal data sources</p>
        </footer>
      </div>
    </div>
  );
} 