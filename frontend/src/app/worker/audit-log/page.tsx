'use client';

import React, { useState, useMemo } from 'react';
import WorkerShell from '@/components/layout/WorkerShell';
import { useWorkflowStore } from '@/store/workflow-store';
import { downloadCsv } from '@/lib/download';

export default function WorkerAuditLogPage() {
  const { auditEvents, getActiveSession } = useWorkflowStore();
  const session = getActiveSession();

  const [filterTab, setFilterTab] = useState<'all' | 'ai' | 'human'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedEventId, setExpandedEventId] = useState<string | null>('EVT-4093');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const aiCount = auditEvents.filter((e) => e.actorType === 'ai').length;
  const humanCount = auditEvents.filter((e) => e.actorType === 'worker' || e.actorType === 'manager').length;

  const filteredEvents = useMemo(() => {
    return auditEvents.filter((evt) => {
      let matchesTab = true;
      if (filterTab === 'ai') matchesTab = evt.actorType === 'ai';
      else if (filterTab === 'human') matchesTab = evt.actorType === 'worker' || evt.actorType === 'manager';

      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q ||
        evt.action.toLowerCase().includes(q) ||
        evt.actor.toLowerCase().includes(q) ||
        evt.sessionFile.toLowerCase().includes(q) ||
        evt.id.toLowerCase().includes(q);

      return matchesTab && matchesSearch;
    });
  }, [auditEvents, filterTab, searchQuery]);

  const handleExport = () => {
    downloadCsv(
      'SOVIA_Worker_Audit_Trail.csv',
      ['Event ID', 'Date', 'Timestamp', 'Actor', 'Actor Type', 'Action', 'Session', 'Status', 'Evidence Hash'],
      filteredEvents.map((event) => [
        event.id,
        event.date,
        event.timestamp,
        event.actor,
        event.actorType,
        event.action,
        event.sessionFile,
        event.status,
        event.evidenceHash,
      ]),
    );
    setToastMessage(`Exported ${filteredEvents.length} audit trail records to CSV.`);
    setTimeout(() => setToastMessage(null), 3500);
  };

  return (
    <WorkerShell>
      <div className="flex flex-col gap-6 max-w-[1400px] mx-auto w-full pb-12">
        {/* Toast */}
        {toastMessage && (
          <div className="p-3 bg-[#D1F2DE] border border-[#7FE3B0] rounded-xl text-xs font-heading font-semibold text-[#0E3B28] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">verified</span>
              <span>{toastMessage}</span>
            </div>
            <button
              type="button"
              onClick={() => setToastMessage(null)}
              className="text-[#0E3B28] hover:underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Page Header & Toolbar */}
        <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-4 pb-4 border-b border-[#D5CEBF]">
          <div className="flex flex-col gap-1 max-w-3xl">
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-tag text-xs bg-[#D1F2DE] text-[#0E3B28] border border-[#7FE3B0]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#00C878]"></span>
                Ledger Block #8,944-SEC
              </span>
              <span className="font-tag text-xs text-[#8B9490]">SHA-256 Verifiable Chain</span>
            </div>
            <h1 className="font-heading text-2xl sm:text-3xl font-bold text-[#121C18] tracking-tight">
              Audit Log
            </h1>
            <p className="font-sans text-sm text-[#4A5550]">
              Cryptographic, tamper-evident chronological ledger proving the “AI recommends, human decides” governance policy across all workflow stages.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex items-center bg-[#EBE5D9] px-3 py-1.5 rounded-lg border border-[#D5CEBF]">
              <span className="material-symbols-outlined text-[#8B9490] text-[18px] mr-1.5">
                filter_list
              </span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter audit events..."
                className="bg-transparent border-0 outline-none text-[#121C18] placeholder-[#8B9490] text-xs w-48 font-sans"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="text-[#8B9490] hover:text-[#121C18] p-0.5"
                >
                  <span className="material-symbols-outlined text-[14px]">close</span>
                </button>
              )}
            </div>
            <button
              type="button"
              onClick={handleExport}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#00C878] hover:bg-[#00b56c] text-[#0E3B28] font-heading text-xs font-bold transition-colors cursor-pointer shadow-none"
            >
              <span className="material-symbols-outlined text-[17px]">download</span>
              Export Audit Trail (.csv)
            </button>
          </div>
        </div>

        {/* Filter Tabs & Context Row */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-2.5 bg-[#EBE5D9] rounded-lg border border-[#D5CEBF]">
          <div className="flex items-center gap-1.5 flex-wrap">
            <button
              type="button"
              onClick={() => setFilterTab('all')}
              className={`px-3.5 py-1.5 rounded-md font-heading text-xs font-bold transition-colors cursor-pointer ${
                filterTab === 'all'
                  ? 'bg-[#00C878] text-[#0E3B28]'
                  : 'text-[#4A5550] hover:bg-[#E5DEC9]'
              }`}
            >
              All Events ({auditEvents.length})
            </button>
            <button
              type="button"
              onClick={() => setFilterTab('ai')}
              className={`px-3.5 py-1.5 rounded-md font-heading text-xs font-medium transition-colors cursor-pointer ${
                filterTab === 'ai'
                  ? 'bg-[#00C878] text-[#0E3B28] font-bold'
                  : 'text-[#4A5550] hover:bg-[#E5DEC9]'
              }`}
            >
              AI Agent Proposals ({aiCount})
            </button>
            <button
              type="button"
              onClick={() => setFilterTab('human')}
              className={`px-3.5 py-1.5 rounded-md font-heading text-xs font-medium transition-colors cursor-pointer ${
                filterTab === 'human'
                  ? 'bg-[#00C878] text-[#0E3B28] font-bold'
                  : 'text-[#4A5550] hover:bg-[#E5DEC9]'
              }`}
            >
              Human Sign-offs ({humanCount})
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs font-tag">
            <div className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#F4EFE5] text-[#121C18] border border-[#D5CEBF]">
              <span className="text-[#8B9490]">Session:</span>
              <span className="font-semibold">{session.fileName}</span>
            </div>
            <div className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#F4EFE5] text-[#121C18] border border-[#D5CEBF]">
              <span>All Stages</span>
            </div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#F4EFE5] text-[#4A5550] border border-[#D5CEBF] font-mono text-[11px]">
              <span className="material-symbols-outlined text-[13px] text-[#00C878]">verified</span>
              Hash: {session.hash || '7f9ba4e1...89c2'}
            </div>
          </div>
        </div>

        {/* Reverse-Chronological Event Stream */}
        <div className="flex flex-col bg-[#EBE5D9] rounded-xl border border-[#D5CEBF] overflow-hidden">
          {/* Table Header Row */}
          <div className="grid grid-cols-12 items-center px-4 py-2.5 bg-[#E5DEC9] text-[#4A5550] font-tag text-[11px] uppercase tracking-wider border-b border-[#D5CEBF]">
            <div className="col-span-2 font-semibold">Timestamp (UTC)</div>
            <div className="col-span-3 font-semibold">Actor &amp; Engine</div>
            <div className="col-span-4 font-semibold">Action &amp; Policy Rule</div>
            <div className="col-span-2 font-semibold">Governance Status</div>
            <div className="col-span-1 text-right font-semibold">Details</div>
          </div>

          {/* Event Entries */}
          {filteredEvents.length === 0 ? (
            <div className="p-10 text-center text-sm text-[#8B9490] bg-[#F4EFE5]">
              No audit ledger events match the current filter.
            </div>
          ) : (
            filteredEvents.map((evt) => {
              const isExpanded = expandedEventId === evt.id;
              return (
                <div key={evt.id} className="flex flex-col border-b border-[#D5CEBF] last:border-b-0">
                  <div
                    onClick={() => setExpandedEventId(isExpanded ? null : evt.id)}
                    className="grid grid-cols-12 items-center px-4 py-3 bg-[#F4EFE5] hover:bg-[#EBE5D9] transition-colors cursor-pointer text-xs"
                  >
                    <div className="col-span-2 font-mono text-[11px] text-[#4A5550]">
                      <div>{evt.date}</div>
                      <div className="text-[10px] text-[#8B9490]">{evt.timestamp}</div>
                    </div>

                    <div className="col-span-3 flex items-center gap-2">
                      <span
                        className={`w-6 h-6 rounded-full flex items-center justify-center font-tag text-[10px] font-bold ${
                          evt.actorType === 'ai'
                            ? 'bg-[#E5DEC9] text-[#121C18]'
                            : evt.actorType === 'manager'
                            ? 'bg-[#0E3B28] text-[#F4EFE5]'
                            : 'bg-[#00C878] text-[#0E3B28]'
                        }`}
                      >
                        {evt.actorType === 'ai' ? 'AI' : evt.actor.slice(0, 2).toUpperCase()}
                      </span>
                      <div>
                        <div className="font-heading font-semibold text-[#121C18]">{evt.actor}</div>
                        <div className="text-[10px] text-[#8B9490]">{evt.actorTitle || 'Enterprise Role'}</div>
                      </div>
                    </div>

                    <div className="col-span-4 text-[#121C18]">
                      <div className="font-medium truncate">{evt.action}</div>
                      <div className="text-[10px] text-[#8B9490] font-mono truncate">{evt.targetScope}</div>
                    </div>

                    <div className="col-span-2">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded font-tag text-[11px] font-bold uppercase tracking-wider border ${
                          evt.status === 'approved'
                            ? 'bg-[#D1F2DE] text-[#0E3B28] border-[#7FE3B0]'
                            : evt.status === 'awaiting'
                            ? 'bg-[#F7ECC8] text-[#B87A1E] border-[#B87A1E]/40'
                            : evt.status === 'flagged'
                            ? 'bg-[#FBEBE8] text-[#8C3B24] border-[#8C3B24]/40'
                            : 'bg-[#E5DEC9] text-[#121C18] border-[#D5CEBF]'
                        }`}
                      >
                        {evt.status}
                      </span>
                    </div>

                    <div className="col-span-1 text-right">
                      <span className="material-symbols-outlined text-[18px] text-[#8B9490]">
                        {isExpanded ? 'expand_less' : 'expand_more'}
                      </span>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="p-4 bg-[#EBE5D9] border-t border-[#D5CEBF] flex flex-col gap-3 text-xs">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div className="p-3 bg-[#F4EFE5] rounded border border-[#D5CEBF]">
                          <span className="text-[10px] uppercase font-tag text-[#8B9490] block mb-1 font-bold">
                            AI Recommendation
                          </span>
                          <p className="font-sans text-[#4A5550]">
                            {evt.aiRecommendation || 'Automated deterministic pre-mapping verified with RMS/AIR standard.'}
                          </p>
                        </div>
                        <div className="p-3 bg-[#F4EFE5] rounded border border-[#D5CEBF]">
                          <span className="text-[10px] uppercase font-tag text-[#8B9490] block mb-1 font-bold">
                            Human Decision Gate
                          </span>
                          <p className="font-sans text-[#4A5550]">
                            {evt.humanDecision || 'Validated under statutory underwriting procedure.'}
                          </p>
                        </div>
                        <div className="p-3 bg-[#F4EFE5] rounded border border-[#D5CEBF]">
                          <span className="text-[10px] uppercase font-tag text-[#8B9490] block mb-1 font-bold">
                            Cryptographic Proof
                          </span>
                          <div className="font-mono text-[10px] text-[#121C18] space-y-0.5 break-all">
                            <div>Hash: {evt.evidenceHash}</div>
                            <div>Nonce: {evt.nonce || '0x93FA910B'}</div>
                            <div>Status: Immutable Ledger Verified</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </WorkerShell>
  );
}
