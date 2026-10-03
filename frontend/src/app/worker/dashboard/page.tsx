'use client';

import React, { useState, useMemo } from 'react';
import Link from 'next/link';
import WorkerShell from '@/components/layout/WorkerShell';
import { useWorkflowStore } from '@/store/workflow-store';

export default function WorkerDashboardPage() {
  const { sessions, setActiveSessionId } = useWorkflowStore();
  const [filter, setFilter] = useState<'all' | 'processing' | 'completed' | 'action-required'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;

  // Dynamic KPI counts from real store state
  const totalCount = sessions.length;
  const processingCount = sessions.filter((s) => s.status === 'processing').length;
  const completedCount = sessions.filter((s) => s.status === 'approved').length;
  const actionRequiredCount = sessions.filter(
    (s) => s.status === 'ready' || s.status === 'returned' || s.status === 'awaiting'
  ).length;

  const filteredSessions = useMemo(() => {
    return sessions.filter((s) => {
      // filter status
      let matchesStatus = true;
      if (filter === 'processing') matchesStatus = s.status === 'processing';
      else if (filter === 'completed') matchesStatus = s.status === 'approved';
      else if (filter === 'action-required') {
        matchesStatus = s.status === 'ready' || s.status === 'returned' || s.status === 'awaiting';
      }

      // search query
      const matchesSearch =
        s.fileName.toLowerCase().includes(searchQuery.toLowerCase().trim()) ||
        s.id.toLowerCase().includes(searchQuery.toLowerCase().trim());
      return matchesStatus && matchesSearch;
    });
  }, [sessions, filter, searchQuery]);

  const totalPages = Math.max(1, Math.ceil(filteredSessions.length / pageSize));
  const safePage = Math.min(currentPage, totalPages);
  const displayedSessions = filteredSessions.slice((safePage - 1) * pageSize, safePage * pageSize);

  const handleFilterChange = (newFilter: 'all' | 'processing' | 'completed' | 'action-required') => {
    setFilter(newFilter);
    setCurrentPage(1);
  };

  const handleSearchChange = (val: string) => {
    setSearchQuery(val);
    setCurrentPage(1);
  };

  return (
    <WorkerShell>
      <div className="flex flex-col w-full max-w-7xl mx-auto space-y-6">
        {/* Section 1: Page Header Row */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="font-heading text-2xl sm:text-3xl font-bold text-[#121C18] tracking-tight">
              Dashboard
            </h1>
            <p className="font-sans text-sm text-[#4A5550] mt-1">
              Overview of SOV ingestion pipelines, agent activity, and active review queues.
            </p>
          </div>
          <div className="flex items-center gap-2 self-start md:self-auto">
            <Link
              href="/worker/upload"
              className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-full bg-[#00C878] text-[#0E3B28] font-heading font-semibold text-sm leading-tight hover:brightness-105 transition-all shadow-none cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">add</span>
              New Analysis
            </Link>
          </div>
        </div>

        {/* Section 2: Row of 4 Flat KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Total Files */}
          <div className="bg-[#EBE5D9] p-4 rounded-lg border border-[#D5CEBF] flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="font-tag text-xs text-[#8B9490] uppercase tracking-wider font-semibold">
                Storage Scope
              </span>
              <span className="material-symbols-outlined text-[#8B9490] text-[20px]">folder_open</span>
            </div>
            <div>
              <div className="font-heading text-3xl font-bold text-[#121C18] leading-none mb-1">
                {totalCount}
              </div>
              <div className="font-heading text-[13px] font-medium text-[#4A5550]">Total Workbooks</div>
              <div className="font-sans text-[11px] text-[#8B9490] mt-0.5">Aggregated SOV submissions</div>
            </div>
          </div>

          {/* Card 2: Processing */}
          <div className="bg-[#EBE5D9] p-4 rounded-lg border border-[#D5CEBF] flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="font-tag text-xs text-[#8B9490] uppercase tracking-wider font-semibold">
                Agent Workload
              </span>
              <span className="material-symbols-outlined text-[#4A5550] text-[20px]">sync</span>
            </div>
            <div>
              <div className="font-heading text-3xl font-bold text-[#121C18] leading-none mb-1">
                {processingCount}
              </div>
              <div className="font-heading text-[13px] font-medium text-[#4A5550]">Processing</div>
              <div className="font-sans text-[11px] text-[#8B9490] mt-0.5">Active agent pipelines</div>
            </div>
          </div>

          {/* Card 3: Completed */}
          <div className="bg-[#EBE5D9] p-4 rounded-lg border border-[#D5CEBF] flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="font-tag text-xs text-[#8B9490] uppercase tracking-wider font-semibold">
                Validated Schema
              </span>
              <span className="material-symbols-outlined text-[#00C878] text-[20px]">check_circle</span>
            </div>
            <div>
              <div className="font-heading text-3xl font-bold text-[#00C878] leading-none mb-1">
                {completedCount}
              </div>
              <div className="font-heading text-[13px] font-medium text-[#0E3B28]">Approved &amp; Completed</div>
              <div className="font-sans text-[11px] text-[#8B9490] mt-0.5">Standardized &amp; locked</div>
            </div>
          </div>

          {/* Card 4: Action Required */}
          <div className="bg-[#EBE5D9] p-4 rounded-lg border border-[#D5CEBF] flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="font-tag text-xs text-[#8B9490] uppercase tracking-wider font-semibold">
                Human Inspection
              </span>
              <span className="material-symbols-outlined text-[#B87A1E] text-[20px]">warning</span>
            </div>
            <div>
              <div className="font-heading text-3xl font-bold text-[#121C18] leading-none mb-1">
                {actionRequiredCount}
              </div>
              <div className="font-heading text-[13px] font-medium text-[#4A5550]">Action Required</div>
              <div className="font-sans text-[11px] text-[#8B9490] mt-0.5">Review / Rework pending</div>
            </div>
          </div>
        </div>

        {/* Section 3: Filter Chips & Search Utility */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          <div className="flex items-center flex-wrap gap-2">
            <button
              type="button"
              onClick={() => handleFilterChange('all')}
              className={`px-3.5 py-1.5 rounded-full font-tag text-xs transition-colors cursor-pointer ${
                filter === 'all'
                  ? 'bg-[#00C878] text-[#0E3B28] font-bold border border-[#00C878]'
                  : 'bg-[#EBE5D9] text-[#8B9490] hover:text-[#121C18] border border-[#D5CEBF]'
              }`}
            >
              All ({totalCount})
            </button>
            <button
              type="button"
              onClick={() => handleFilterChange('processing')}
              className={`px-3.5 py-1.5 rounded-full font-tag text-xs transition-colors cursor-pointer ${
                filter === 'processing'
                  ? 'bg-[#00C878] text-[#0E3B28] font-bold border border-[#00C878]'
                  : 'bg-[#EBE5D9] text-[#8B9490] hover:text-[#121C18] border border-[#D5CEBF]'
              }`}
            >
              Processing ({processingCount})
            </button>
            <button
              type="button"
              onClick={() => handleFilterChange('completed')}
              className={`px-3.5 py-1.5 rounded-full font-tag text-xs transition-colors cursor-pointer ${
                filter === 'completed'
                  ? 'bg-[#00C878] text-[#0E3B28] font-bold border border-[#00C878]'
                  : 'bg-[#EBE5D9] text-[#8B9490] hover:text-[#121C18] border border-[#D5CEBF]'
              }`}
            >
              Completed ({completedCount})
            </button>
            <button
              type="button"
              onClick={() => handleFilterChange('action-required')}
              className={`px-3.5 py-1.5 rounded-full font-tag text-xs transition-colors cursor-pointer ${
                filter === 'action-required'
                  ? 'bg-[#00C878] text-[#0E3B28] font-bold border border-[#00C878]'
                  : 'bg-[#EBE5D9] text-[#8B9490] hover:text-[#121C18] border border-[#D5CEBF]'
              }`}
            >
              Review Required ({actionRequiredCount})
            </button>
          </div>

          <div className="relative flex items-center min-w-[260px]">
            <span className="material-symbols-outlined absolute left-3 text-[#8B9490] text-[18px]">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="Search files by name or ID..."
              className="w-full pl-9 pr-8 py-1.5 rounded-full bg-[#EBE5D9] text-[#121C18] placeholder-[#8B9490] text-[13px] border border-[#D5CEBF] outline-none focus:border-[#00C878]"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => handleSearchChange('')}
                className="absolute right-3 text-[#8B9490] hover:text-[#121C18]"
              >
                <span className="material-symbols-outlined text-[16px]">close</span>
              </button>
            )}
          </div>
        </div>

        {/* Section 4: Recent Analyses Dense Table Container */}
        <div className="bg-[#F4EFE5] rounded-lg border border-[#D5CEBF] overflow-hidden">
          <div className="px-5 py-3.5 bg-[#F4EFE5] border-b border-[#D5CEBF] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="font-heading text-base font-semibold text-[#121C18]">Recent Analyses</h2>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-[#EBE5D9] text-[#4A5550] font-tag text-[11px]">
                {filteredSessions.length} {filteredSessions.length === 1 ? 'file' : 'files'} matching
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-[#8B9490] font-tag text-[12px]">
              <span className="material-symbols-outlined text-[16px]">tune</span>
              <span>Standardized Schema: CRE-v2025</span>
            </div>
          </div>

          <div className="overflow-x-auto w-full">
            <table className="w-full text-left font-sans text-[13px]">
              <thead>
                <tr className="bg-[#EBE5D9] text-[#4A5550] font-heading text-[12px] uppercase tracking-wider border-b border-[#D5CEBF]">
                  <th className="py-3 px-5 font-semibold">File Name &amp; Properties</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Last Updated</th>
                  <th className="py-3 px-5 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EBE5D9]">
                {displayedSessions.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-8 px-5 text-center text-sm text-[#8B9490]">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <span className="material-symbols-outlined text-[28px] text-[#8B9490]">
                          search_off
                        </span>
                        <span>No SOV sessions found matching the current search or filter.</span>
                        {(searchQuery || filter !== 'all') && (
                          <button
                            type="button"
                            onClick={() => {
                              setFilter('all');
                              setSearchQuery('');
                              setCurrentPage(1);
                            }}
                            className="mt-1 text-xs font-heading font-semibold text-[#0E3B28] underline cursor-pointer"
                          >
                            Reset filters
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ) : (
                  displayedSessions.map((session) => {
                    const isActionRequired = session.status === 'ready' || session.status === 'returned';
                    const isProcessing = session.status === 'processing';
                    const isAwaiting = session.status === 'awaiting';
                    const isCompleted = session.status === 'approved';

                    return (
                      <tr
                        key={session.id}
                        className="bg-[#F4EFE5] hover:bg-[#EBE5D9] transition-colors"
                      >
                        <td className="py-3.5 px-5">
                          <div className="flex items-center gap-3 min-w-0">
                            <span className="material-symbols-outlined text-[#8B9490] text-[20px] shrink-0">
                              table_chart
                            </span>
                            <div className="min-w-0">
                              <div className="font-heading font-semibold text-[#121C18] truncate">
                                {session.fileName}
                              </div>
                              <div className="font-tag text-[11px] text-[#8B9490]">
                                {session.id} · {session.fileSize} · {session.sheetCount} Sheets · {session.rowCount} Rows
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="py-3.5 px-4 whitespace-nowrap">
                          {isActionRequired && (
                            <span
                              className={`inline-flex items-center px-2.5 py-1 rounded-full font-tag text-[11px] font-bold tracking-wide border ${
                                session.status === 'returned'
                                  ? 'bg-[#FBEBE8] text-[#8C3B24] border-[#8C3B24]/40'
                                  : 'bg-[#D1F2DE] text-[#0E3B28] border-[#7FE3B0]'
                              }`}
                            >
                              {session.status === 'returned' ? 'Returned / Rework' : 'Ready for Review'}
                            </span>
                          )}
                          {isProcessing && (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-tag text-[11px] font-semibold bg-[#E5DEC9] text-[#121C18] border border-[#D5CEBF] tracking-wide">
                              <span className="w-1.5 h-1.5 rounded-full bg-[#00C878] animate-pulse"></span>
                              Processing
                            </span>
                          )}
                          {isAwaiting && (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-tag text-[11px] font-semibold bg-[#F7ECC8] text-[#B87A1E] border border-[#B87A1E]/40 tracking-wide">
                              <span className="material-symbols-outlined text-[13px]">schedule</span>
                              Awaiting Manager
                            </span>
                          )}
                          {isCompleted && (
                            <span className="inline-flex items-center px-2.5 py-1 rounded-full font-tag text-[11px] font-semibold bg-[#00C878] text-[#0E3B28] tracking-wide">
                              Completed
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-[#4A5550] whitespace-nowrap text-xs">
                          {session.updatedAt}
                        </td>
                        <td className="py-3.5 px-5 text-right whitespace-nowrap">
                          {isActionRequired && (
                            <Link
                              href="/worker/data-quality"
                              onClick={() => setActiveSessionId(session.id)}
                              className="inline-flex items-center gap-1 font-heading text-[13px] font-semibold text-[#0E3B28] hover:text-[#00C878] transition-colors"
                            >
                              Resume Review{' '}
                              <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                            </Link>
                          )}
                          {isProcessing && (
                            <Link
                              href="/worker/analysis"
                              onClick={() => setActiveSessionId(session.id)}
                              className="inline-flex items-center gap-1 font-heading text-[13px] font-semibold text-[#4A5550] hover:text-[#121C18] transition-colors"
                            >
                              View Stream{' '}
                              <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                            </Link>
                          )}
                          {(isCompleted || isAwaiting) && (
                            <Link
                              href="/worker/output"
                              onClick={() => setActiveSessionId(session.id)}
                              className="inline-flex items-center gap-1 font-heading text-[13px] font-semibold text-[#4A5550] hover:text-[#121C18] transition-colors"
                            >
                              Download / Output{' '}
                              <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                            </Link>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Table Pagination footer */}
          <div className="px-5 py-3 bg-[#EBE5D9] border-t border-[#D5CEBF] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#4A5550]">
            <span>
              Showing {displayedSessions.length > 0 ? (safePage - 1) * pageSize + 1 : 0} to{' '}
              {Math.min(safePage * pageSize, filteredSessions.length)} of {filteredSessions.length} entries
            </span>
            <div className="flex gap-1.5">
              <button
                type="button"
                disabled={safePage <= 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                className="px-2.5 py-1 rounded border border-[#D5CEBF] bg-[#F4EFE5] text-[#121C18] disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#EBE5D9] cursor-pointer"
              >
                Previous
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((pg) => (
                <button
                  key={pg}
                  type="button"
                  onClick={() => setCurrentPage(pg)}
                  className={`px-2.5 py-1 rounded border border-[#D5CEBF] text-xs font-bold cursor-pointer ${
                    safePage === pg
                      ? 'bg-[#00C878] text-[#0E3B28] border-[#00C878]'
                      : 'bg-[#F4EFE5] text-[#121C18] hover:bg-[#EBE5D9]'
                  }`}
                >
                  {pg}
                </button>
              ))}
              <button
                type="button"
                disabled={safePage >= totalPages}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                className="px-2.5 py-1 rounded border border-[#D5CEBF] bg-[#F4EFE5] text-[#121C18] disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#EBE5D9] cursor-pointer"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </WorkerShell>
  );
}
