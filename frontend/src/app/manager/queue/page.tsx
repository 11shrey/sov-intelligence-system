'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import ManagerShell from '@/components/layout/ManagerShell';
import { useWorkflowStore } from '@/store/workflow-store';

export default function ManagerApprovalQueuePage() {
  const router = useRouter();
  const { sessions, setActiveSessionId } = useWorkflowStore();
  const [statusFilter, setStatusFilter] = useState<'all' | 'awaiting' | 'approved' | 'returned'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredSessions = sessions.filter((s) => {
    let matchesStatus = true;
    if (statusFilter === 'awaiting') matchesStatus = s.status === 'awaiting' || s.status === 'ready';
    else if (statusFilter === 'approved') matchesStatus = s.status === 'approved';
    else if (statusFilter === 'returned') matchesStatus = s.status === 'returned';

    const matchesSearch =
      s.fileName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.workerName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.id.toLowerCase().includes(searchQuery.toLowerCase());

    return matchesStatus && matchesSearch;
  });

  const handleOpenReview = (id: string) => {
    setActiveSessionId(id);
    router.push(`/manager/review?id=${id}`);
  };

  const pendingCount = sessions.filter((s) => s.status === 'awaiting' || s.status === 'ready').length;
  const approvedCount = sessions.filter((s) => s.status === 'approved').length;
  const returnedCount = sessions.filter((s) => s.status === 'returned').length;

  return (
    <ManagerShell>
      <div className="flex flex-col w-full space-y-5">
        {/* Header Strip */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#D5CEBF]">
          <div>
            <div className="flex items-center gap-2 text-[11px] font-tag uppercase tracking-wider text-[#8B9490] mb-1">
              <span>Manager Scope</span>
              <span>/</span>
              <span className="text-[#0E3B28] font-bold">Governance Gate L4</span>
            </div>
            <h1 className="font-heading text-2xl sm:text-3xl font-bold text-[#121C18] tracking-tight">
              Approval Queue
            </h1>
            <p className="font-sans text-xs sm:text-sm text-[#4A5550] mt-0.5">
              Worker SOV submissions requiring dual-control manager inspection before standardized release.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full font-tag text-xs font-bold bg-[#F7ECC8] text-[#B87A1E] border border-[#D5CEBF]">
              {pendingCount} Awaiting Authorization
            </span>
          </div>
        </div>

        {/* Filter Tabs & Search Bar */}
        <div className="bg-[#EBE5D9] p-3 rounded-lg border border-[#D5CEBF] flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 flex-wrap">
            <button
              type="button"
              onClick={() => setStatusFilter('all')}
              className={`px-3 py-1.5 rounded-md text-xs font-tag font-bold transition-colors cursor-pointer ${
                statusFilter === 'all'
                  ? 'bg-[#00C878] text-[#0E3B28]'
                  : 'bg-[#F4EFE5] text-[#4A5550] border border-[#D5CEBF] hover:bg-[#EBE5D9]'
              }`}
            >
              All Submissions ({sessions.length})
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter('awaiting')}
              className={`px-3 py-1.5 rounded-md text-xs font-tag font-bold transition-colors cursor-pointer ${
                statusFilter === 'awaiting'
                  ? 'bg-[#00C878] text-[#0E3B28]'
                  : 'bg-[#F4EFE5] text-[#4A5550] border border-[#D5CEBF] hover:bg-[#EBE5D9]'
              }`}
            >
              Pending Review ({pendingCount})
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter('approved')}
              className={`px-3 py-1.5 rounded-md text-xs font-tag font-bold transition-colors cursor-pointer ${
                statusFilter === 'approved'
                  ? 'bg-[#00C878] text-[#0E3B28]'
                  : 'bg-[#F4EFE5] text-[#4A5550] border border-[#D5CEBF] hover:bg-[#EBE5D9]'
              }`}
            >
              Approved ({approvedCount})
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter('returned')}
              className={`px-3 py-1.5 rounded-md text-xs font-tag font-bold transition-colors cursor-pointer ${
                statusFilter === 'returned'
                  ? 'bg-[#00C878] text-[#0E3B28]'
                  : 'bg-[#F4EFE5] text-[#4A5550] border border-[#D5CEBF] hover:bg-[#EBE5D9]'
              }`}
            >
              Returned for Rework ({returnedCount})
            </button>
          </div>

          <div className="relative flex items-center min-w-[260px]">
            <span className="material-symbols-outlined text-[#8B9490] text-[18px] absolute left-2.5">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search queue..."
              className="w-full bg-[#F4EFE5] border border-[#D5CEBF] text-[#121C18] placeholder-[#8B9490] text-xs rounded-lg pl-8 pr-3 py-1.5 outline-none focus:border-[#00C878]"
            />
          </div>
        </div>

        {/* Queue Table */}
        <div className="bg-[#F4EFE5] border border-[#D5CEBF] rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-sans text-xs border-collapse">
              <thead>
                <tr className="bg-[#EBE5D9] text-[#4A5550] font-heading text-[11px] uppercase tracking-wider border-b border-[#D5CEBF]">
                  <th className="py-3 px-4 font-semibold">Workbook &amp; Session</th>
                  <th className="py-3 px-4 font-semibold">Submitted By</th>
                  <th className="py-3 px-4 font-semibold">Records &amp; Confidence</th>
                  <th className="py-3 px-4 font-semibold">Queue Status</th>
                  <th className="py-3 px-4 font-semibold">SLA / Wait Time</th>
                  <th className="py-3 px-4 font-semibold text-right">Review Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D5CEBF]">
                {filteredSessions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 px-4 text-center">
                      <div className="flex flex-col items-center justify-center">
                        <span className="material-symbols-outlined text-[#8B9490] text-[40px] mb-2">
                          inbox
                        </span>
                        <div className="font-heading font-bold text-sm text-[#121C18]">
                          No submissions match your filters
                        </div>
                        <p className="font-sans text-xs text-[#4A5550] max-w-sm mt-1">
                          Try adjusting your search terms or status filter tab to find queue items.
                        </p>
                        <button
                          type="button"
                          onClick={() => {
                            setStatusFilter('all');
                            setSearchQuery('');
                          }}
                          className="mt-3 px-3 py-1.5 rounded-lg text-xs font-bold bg-[#EBE5D9] hover:bg-[#D5CEBF] text-[#0E3B28] cursor-pointer"
                        >
                          Reset filters
                        </button>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredSessions.map((s) => {
                    const isAwaiting = s.status === 'awaiting' || s.status === 'ready';
                    const isApproved = s.status === 'approved';
                    const isReturned = s.status === 'returned';

                    return (
                      <tr
                        key={s.id}
                        className="bg-[#F4EFE5] hover:bg-[#EBE5D9] transition-colors cursor-pointer"
                        onClick={() => handleOpenReview(s.id)}
                      >
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2.5">
                            <span className="material-symbols-outlined text-[#8B9490] text-[20px]">
                              description
                            </span>
                            <div>
                              <div className="font-heading font-bold text-xs text-[#121C18]">
                                {s.fileName}
                              </div>
                              <div className="font-mono text-[10px] text-[#8B9490]">{s.id}</div>
                            </div>
                          </div>
                        </td>

                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-[#0E3B28] text-[#F4EFE5] font-tag font-bold text-[9px] flex items-center justify-center">
                              {s.workerAvatar}
                            </span>
                            <span className="font-heading font-medium text-[#121C18]">
                              {s.workerName}
                            </span>
                          </div>
                        </td>

                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-[#121C18]">{s.rowCount} rows</span>
                            <span>·</span>
                            <span className="font-tag text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#D1F2DE] text-[#0E3B28] border border-[#7FE3B0]">
                              {s.confidence}% Conf.
                            </span>
                          </div>
                        </td>

                        <td className="py-3.5 px-4">
                          {isAwaiting && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-tag font-bold bg-[#F7ECC8] text-[#B87A1E] border border-[#D5CEBF]">
                              Awaiting Review
                            </span>
                          )}
                          {isApproved && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-tag font-bold bg-[#D1F2DE] text-[#0E3B28] border border-[#7FE3B0]">
                              Approved
                            </span>
                          )}
                          {isReturned && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-tag font-bold bg-[#FBEBE8] text-[#8C3B24] border border-[#8C3B24]/40">
                              Returned for Rework
                            </span>
                          )}
                        </td>

                        <td className="py-3.5 px-4">
                          <span className="font-tag text-xs text-[#4A5550]">
                            {isAwaiting ? '2h 14m waiting' : s.updatedAt}
                          </span>
                        </td>

                        <td className="py-3.5 px-4 text-right">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenReview(s.id);
                            }}
                            className="px-3.5 py-1.5 rounded-full font-heading text-xs font-bold bg-[#00C878] text-[#0E3B28] hover:bg-[#00b56c] transition-colors inline-flex items-center gap-1 cursor-pointer shadow-none"
                          >
                            <span>Review Session</span>
                            <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <div className="p-3 bg-[#EBE5D9] border-t border-[#D5CEBF] flex items-center justify-between text-xs text-[#4A5550] font-tag">
            <span>Displaying {filteredSessions.length} active queue entries</span>
            <span>All actions are cryptographically authenticated under L4 policy</span>
          </div>
        </div>
      </div>
    </ManagerShell>
  );
}
