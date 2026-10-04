'use client';

import React, { Suspense, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import ManagerShell from '@/components/layout/ManagerShell';
import { useWorkflowStore } from '@/store/workflow-store';
import { useAuthStore } from '@/store/auth-store';
import { SessionWorkflowStatus } from '@/types';

function ManagerSessionReviewContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('id') || 'SOV-2026-1042';

  const {
    sessions,
    managerApproveSession,
    managerReturnSession,
    setSessionStatus,
  } = useWorkflowStore();
  const { user } = useAuthStore();

  const session = sessions.find((s) => s.id === sessionId) || sessions[0];
  const [reviewState, setReviewState] = useState<SessionWorkflowStatus>(session.status || 'awaiting');

  // Modals
  const [approveModalOpen, setApproveModalOpen] = useState(false);
  const [returnModalOpen, setReturnModalOpen] = useState(false);
  const [returnReason, setReturnReason] = useState(
    'Storeys reconciliation required on Row 142. Please verify with municipal permit filings rather than default assumption.'
  );

  const managerName = user?.name || 'S. Reynolds';

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setApproveModalOpen(false);
        setReturnModalOpen(false);
      }
    };
    if (approveModalOpen || returnModalOpen) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [approveModalOpen, returnModalOpen]);

  const handleApplyState = (st: SessionWorkflowStatus) => {
    setReviewState(st);
    setSessionStatus(session.id, st);
  };

  const handleConfirmApproval = () => {
    managerApproveSession(session.id, managerName);
    setReviewState('approved');
    setApproveModalOpen(false);
  };

  const handleConfirmReturn = () => {
    managerReturnSession(session.id, returnReason, managerName);
    setReviewState('returned');
    setReturnModalOpen(false);
  };

  return (
    <ManagerShell>
      <div className="flex flex-col w-full text-[#121C18] space-y-5 pb-16">
        {/* Top Contextual Breadcrumb & Metadata Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 gap-3 border-b border-[#D5CEBF]">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2 text-[11px] font-tag uppercase tracking-wider text-[#8B9490]">
              <Link href="/manager/queue" className="hover:text-[#121C18] flex items-center gap-1 transition-colors">
                Approval Queue
              </Link>
              <span>/</span>
              <span className="text-[#0E3B28] font-semibold">Session Review</span>
              <span>/</span>
              <span className="font-mono text-[10px] text-[#4A5550]">{session.id}</span>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-xl md:text-2xl font-bold font-heading text-[#121C18] tracking-tight">
                {session.fileName}
              </h1>

              {/* Status Badge */}
              <span
                className={`px-2.5 py-0.5 rounded text-[11px] font-semibold font-tag uppercase tracking-wider border ${
                  reviewState === 'approved'
                    ? 'bg-[#D1F2DE] text-[#0E3B28] border-[#7FE3B0]'
                    : reviewState === 'returned'
                    ? 'bg-[#FBEBE8] text-[#8C3B24] border-[#8C3B24]/40'
                    : 'bg-[#F7ECC8] text-[#B87A1E] border-[#E2D1A8]'
                }`}
              >
                {reviewState === 'approved'
                  ? 'APPROVED'
                  : reviewState === 'returned'
                  ? 'RETURNED'
                  : 'AWAITING REVIEW'}
              </span>

              <span className="text-[11px] text-[#8B9490] font-tag">|</span>
              <span className="text-xs text-[#4A5550]">
                Submitted by <strong className="text-[#121C18] font-semibold">{session.workerName}</strong> (CRE Portfolio Specialist)
              </span>
            </div>
          </div>

          {/* Actions & Simulator Pill */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#EBE5D9] border border-[#D5CEBF] text-xs">
              <span className="text-[10px] uppercase font-tag text-[#8B9490]">Review State:</span>
              <select
                value={reviewState}
                onChange={(e) => handleApplyState(e.target.value as SessionWorkflowStatus)}
                className="bg-transparent font-medium text-xs text-[#121C18] focus:outline-none cursor-pointer"
              >
                <option value="awaiting">1. Awaiting Review (Default)</option>
                <option value="approved">2. Approved State</option>
                <option value="returned">3. Returned for Revision</option>
              </select>
            </div>
            <Link
              href="/manager/queue"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border border-[#3F6B52] bg-transparent text-xs font-semibold text-[#0E3B28] hover:bg-[#EBE5D9] transition-colors"
            >
              <span className="material-symbols-outlined text-[16px]">arrow_back</span>
              <span>Back to Queue</span>
            </Link>
          </div>
        </div>

        {/* Manager Rework Notice Banner (shown when Returned) */}
        {reviewState === 'returned' && (
          <div className="p-3.5 bg-[#FBEBE8] border border-[#8C3B24] rounded-lg text-xs flex items-start justify-between gap-4">
            <div className="flex items-start gap-2.5">
              <span className="material-symbols-outlined text-[#8C3B24] text-[18px] shrink-0 mt-0.5">
                rate_review
              </span>
              <div>
                <span className="font-semibold text-[#8C3B24] block mb-0.5">
                  Session Returned to {session.workerName} for Remediation
                </span>
                <p className="text-[#4A5550]">
                  &ldquo;{session.returnRemarks || returnReason}&rdquo;
                </p>
              </div>
            </div>
            <span className="text-[10px] font-tag uppercase text-[#8C3B24] bg-[#F4EFE5] px-2 py-0.5 rounded border border-[#8C3B24] whitespace-nowrap">
              Flagged: Oct 2, 10:48 AM
            </span>
          </div>
        )}

        {/* Compact Session Information Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 text-xs">
          <div className="p-2.5 rounded bg-[#F4EFE5] border border-[#D5CEBF] flex flex-col justify-between">
            <span className="text-[10px] font-tag uppercase tracking-wider text-[#8B9490]">
              Target Portfolio
            </span>
            <span className="font-semibold text-[#121C18] truncate mt-1">{session.fileName}</span>
            <span className="text-[10px] font-mono text-[#4A5550]">.xlsx (Sheet 1)</span>
          </div>
          <div className="p-2.5 rounded bg-[#F4EFE5] border border-[#D5CEBF] flex flex-col justify-between">
            <span className="text-[10px] font-tag uppercase tracking-wider text-[#8B9490]">
              Prepared By
            </span>
            <span className="font-semibold text-[#121C18] truncate mt-1">{session.workerName}</span>
            <span className="text-[10px] text-[#4A5550]">ID: {session.workerId}</span>
          </div>
          <div className="p-2.5 rounded bg-[#F4EFE5] border border-[#D5CEBF] flex flex-col justify-between">
            <span className="text-[10px] font-tag uppercase tracking-wider text-[#8B9490]">
              Session ID
            </span>
            <span className="font-mono font-semibold text-[#121C18] mt-1">{session.id}</span>
            <span className="text-[10px] text-[#8B9490]">Gov Level 4</span>
          </div>
          <div className="p-2.5 rounded bg-[#F4EFE5] border border-[#D5CEBF] flex flex-col justify-between">
            <span className="text-[10px] font-tag uppercase tracking-wider text-[#8B9490]">
              Submitted Timestamp
            </span>
            <span className="font-semibold text-[#121C18] mt-1">Oct 2, 2026</span>
            <span className="text-[10px] text-[#4A5550]">10:42 AM EST</span>
          </div>
          <div className="p-2.5 rounded bg-[#F4EFE5] border border-[#D5CEBF] flex flex-col justify-between">
            <span className="text-[10px] font-tag uppercase tracking-wider text-[#8B9490]">
              Data Volume
            </span>
            <span className="font-semibold text-[#121C18] mt-1">{session.rowCount} Rows</span>
            <span className="text-[10px] text-[#4A5550]">17 Schema Fields</span>
          </div>
          <div className="p-2.5 rounded bg-[#F4EFE5] border border-[#D5CEBF] flex flex-col justify-between">
            <span className="text-[10px] font-tag uppercase tracking-wider text-[#8B9490]">
              Aggregate Confidence
            </span>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-[#D1F2DE] text-[#0E3B28] border border-[#7FE3B0]">
                {session.confidence}% HIGH
              </span>
            </div>
            <span className="text-[10px] text-[#3F6B52]">Deterministic Pass</span>
          </div>
        </div>

        {/* 5-Metric Retrained Audit Summary Strip */}
        <div className="p-3 bg-[#EBE5D9] border border-[#D5CEBF] rounded-lg flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#00C878]"></span>
            <span className="text-[#8B9490] font-tag uppercase text-[10px]">Mapping Coverage:</span>
            <span className="font-semibold text-[#121C18]">17 / 17 fields mapped (100%)</span>
          </div>
          <div className="h-3 w-px bg-[#D5CEBF] hidden md:block"></div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#B87A1E]"></span>
            <span className="text-[#8B9490] font-tag uppercase text-[10px]">Data Quality:</span>
            <span className="font-semibold text-[#121C18]">3 issues audited (1 Crit, 1 Req, 1 Warn)</span>
          </div>
          <div className="h-3 w-px bg-[#D5CEBF] hidden md:block"></div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#00C878]"></span>
            <span className="text-[#8B9490] font-tag uppercase text-[10px]">Transformations:</span>
            <span className="font-semibold text-[#121C18]">12 approved pipeline ops</span>
          </div>
          <div className="h-3 w-px bg-[#D5CEBF] hidden md:block"></div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#00C878]"></span>
            <span className="text-[#8B9490] font-tag uppercase text-[10px]">Unresolved Flags:</span>
            <span className="font-semibold text-[#0E3B28]">0 remaining</span>
          </div>
          <div className="h-3 w-px bg-[#D5CEBF] hidden md:block"></div>
          <div className="flex items-center gap-1.5 font-mono text-[10px] text-[#4A5550]">
            <span className="material-symbols-outlined text-[15px] text-[#00C878]">verified</span>
            <span>Hash: SHA256:8f4a..99c2</span>
          </div>
        </div>

        {/* Section 1: Transformation Review Table */}
        <div className="border border-[#D5CEBF] rounded-xl bg-[#F4EFE5] overflow-hidden">
          <div className="px-4 py-3 bg-[#EBE5D9] border-b border-[#D5CEBF] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="font-heading font-semibold text-sm text-[#121C18]">
                Transformation Pipeline Audit (12 Operations Applied)
              </h2>
              <span className="text-[10px] font-tag px-2 py-0.5 rounded bg-[#E5DEC9] border border-[#D5CEBF] text-[#4A5550]">
                Read-Only L4 Verification
              </span>
            </div>
            <div className="text-[11px] text-[#8B9490]">Showing 7 representative field mutations</div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-[#E5DEC9] border-b border-[#D5CEBF] text-[#4A5550] text-[10px] font-tag uppercase tracking-wider">
                  <th className="py-2.5 px-3 font-semibold">Source Field</th>
                  <th className="py-2.5 px-3 font-semibold">Target Canonical Field</th>
                  <th className="py-2.5 px-3 font-semibold">Before (Raw SOV)</th>
                  <th className="py-2.5 px-3 font-semibold">After (Sanitized Canonical)</th>
                  <th className="py-2.5 px-3 font-semibold">Confidence</th>
                  <th className="py-2.5 px-3 font-semibold">AI Transformation Rationale</th>
                  <th className="py-2.5 px-3 font-semibold">Worker Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D5CEBF] text-[#121C18]">
                {[
                  {
                    src: 'Property Addr.',
                    target: 'Property Address',
                    before: '"42 MG Rd."',
                    after: '"42 MG Rd."',
                    conf: 98,
                    rationale: 'Normalized address punctuation and whitespace trailing string',
                  },
                  {
                    src: 'Yr Built',
                    target: 'Year Built',
                    before: '"2018" (string)',
                    after: '2018 (int4)',
                    conf: 96,
                    rationale: 'Cast text year representation to 4-digit calendar integer ISO-8601',
                  },
                  {
                    src: 'No. Floors',
                    target: 'Storeys',
                    before: '"3 floors"',
                    after: '3 (int)',
                    conf: 91,
                    rationale: 'Extracted leading numeric digit from natural language string',
                  },
                  {
                    src: 'Replacement_Cost',
                    target: 'Building Replacement Cost',
                    before: '"$1,450,000 (est)"',
                    after: '$1,450,000.00',
                    conf: 95,
                    rationale: 'Stripped annotation suffix "(est)", normalized USD float currency format',
                  },
                  {
                    src: 'Occ_Code',
                    target: 'Occupancy Code',
                    before: '"COMM-OFF"',
                    after: 'Commercial - Office (04)',
                    conf: 92,
                    rationale: 'Standardized ISO commercial occupancy classification dictionary lookup',
                  },
                  {
                    src: 'Const_Type',
                    target: 'Construction Class',
                    before: '"NC-3"',
                    after: '3 - Masonry Non-Combustible',
                    conf: 94,
                    rationale: 'Normalized broker short-hand into standardized ISO construction class',
                  },
                ].map((row, idx) => (
                  <tr key={idx} className="hover:bg-[#EBE5D9]/50 transition-colors">
                    <td className="py-2 px-3 font-mono text-[11px] text-[#4A5550]">{row.src}</td>
                    <td className="py-2 px-3 font-semibold text-[#121C18]">{row.target}</td>
                    <td className="py-2 px-3 font-mono text-[11px] bg-[#EBE5D9]/40">{row.before}</td>
                    <td className="py-2 px-3 font-mono text-[11px] font-semibold text-[#0E3B28] bg-[#D1F2DE]/50">
                      {row.after}
                    </td>
                    <td className="py-2 px-3">
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#D1F2DE] text-[#0E3B28] border border-[#7FE3B0]">
                        {row.conf}%
                      </span>
                    </td>
                    <td className="py-2 px-3 text-[11px] text-[#4A5550]">{row.rationale}</td>
                    <td className="py-2 px-3">
                      <span className="inline-flex items-center gap-1 text-[10px] font-tag uppercase text-[#0E3B28] font-bold">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#00C878]"></span> Approved
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Bottom Decision Dock / Action Bar */}
        <div className="sticky bottom-4 z-40 bg-[#EBE5D9] border border-[#D5CEBF] rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#0E3B28] text-[#F4EFE5] font-tag font-bold text-xs flex items-center justify-center">
              SR
            </div>
            <div>
              <div className="text-xs font-heading font-bold text-[#121C18]">
                {managerName} (Level 4 Risk Signatory)
              </div>
              <div className="text-[11px] text-[#4A5550]">
                {reviewState === 'approved' ? (
                  <span className="text-[#0E3B28] font-bold">Authorized &amp; Signed</span>
                ) : reviewState === 'returned' ? (
                  <span className="text-[#8C3B24] font-bold">Returned for Worker Rework</span>
                ) : (
                  <span className="text-[#B87A1E]">Awaiting Manager Decision</span>
                )}
              </div>
            </div>
          </div>

          {/* Action buttons */}
          {reviewState === 'awaiting' ? (
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setReturnModalOpen(true)}
                className="px-4 py-2 rounded-full border border-[#8C3B24] bg-[#F4EFE5] text-[#8C3B24] hover:bg-[#FBEBE8] font-heading text-xs font-bold transition-colors cursor-pointer"
              >
                Return for Revision
              </button>
              <button
                type="button"
                onClick={() => setApproveModalOpen(true)}
                className="px-5 py-2 rounded-full bg-[#00C878] hover:bg-[#00b56c] text-[#0E3B28] font-heading text-xs font-bold transition-colors cursor-pointer shadow-none"
              >
                Authorize &amp; Approve
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <span className="text-xs font-tag text-[#4A5550]">
                Decision recorded · Audit Ledger Nonce #0x932F
              </span>
              <button
                type="button"
                onClick={() => handleApplyState('awaiting')}
                className="px-3 py-1.5 rounded-full border border-[#D5CEBF] bg-[#F4EFE5] text-[#121C18] text-xs font-heading hover:bg-[#EBE5D9] cursor-pointer"
              >
                Re-evaluate Decision
              </button>
            </div>
          )}
        </div>

        {/* Approve Modal */}
        {approveModalOpen && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
            onClick={() => setApproveModalOpen(false)}
          >
            <div
              className="w-full max-w-md bg-[#F4EFE5] border border-[#D5CEBF] rounded-xl p-6 flex flex-col gap-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between pb-3 border-b border-[#D5CEBF]">
                <h3 className="font-heading font-bold text-base text-[#121C18]">
                  Authorize &amp; Approve SOV
                </h3>
                <button
                  type="button"
                  onClick={() => setApproveModalOpen(false)}
                  className="text-[#8B9490] hover:text-[#121C18]"
                >
                  <span className="material-symbols-outlined text-[20px]">close</span>
                </button>
              </div>

              <p className="text-xs text-[#4A5550] leading-relaxed">
                You are executing Level 4 dual-custody authorization on <strong className="text-[#121C18]">{session.fileName}</strong>. This marks all 17 schema standardizations as production-cleared and enables direct export for underwriting.
              </p>

              <div className="p-3 bg-[#EBE5D9] border border-[#D5CEBF] rounded-lg text-xs font-tag space-y-1">
                <div className="flex justify-between">
                  <span>Signatory:</span>
                  <strong className="text-[#121C18]">{managerName}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Audit Policy:</span>
                  <span className="text-[#0E3B28] font-bold">Zero Silent Drops Guarantee</span>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setApproveModalOpen(false)}
                  className="px-4 py-2 rounded-full border border-[#D5CEBF] text-xs font-heading"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmApproval}
                  className="px-5 py-2 rounded-full bg-[#00C878] text-[#0E3B28] font-heading font-bold text-xs hover:bg-[#00b56c]"
                >
                  Confirm &amp; Sign Approval
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Return Modal */}
        {returnModalOpen && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
            onClick={() => setReturnModalOpen(false)}
          >
            <div
              className="w-full max-w-md bg-[#F4EFE5] border border-[#D5CEBF] rounded-xl p-6 flex flex-col gap-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between pb-3 border-b border-[#D5CEBF]">
                <h3 className="font-heading font-bold text-base text-[#8C3B24]">
                  Return Session for Remediation
                </h3>
                <button
                  type="button"
                  onClick={() => setReturnModalOpen(false)}
                  className="text-[#8B9490] hover:text-[#121C18]"
                >
                  <span className="material-symbols-outlined text-[20px]">close</span>
                </button>
              </div>

              <p className="text-xs text-[#4A5550]">
                Specify why this SOV requires rework before it can be authorized. The worker ({session.workerName}) will receive this feedback instantaneously.
              </p>

              <div>
                <label className="block text-xs font-heading font-semibold text-[#121C18] mb-1">
                  Manager Remarks / Instructions
                </label>
                <textarea
                  rows={3}
                  value={returnReason}
                  onChange={(e) => setReturnReason(e.target.value)}
                  className="w-full bg-[#EBE5D9] border border-[#D5CEBF] rounded-lg p-2.5 text-xs text-[#121C18] outline-none focus:border-[#8C3B24]"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setReturnModalOpen(false)}
                  className="px-4 py-2 rounded-full border border-[#D5CEBF] text-xs font-heading"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmReturn}
                  className="px-5 py-2 rounded-full bg-[#8C3B24] text-[#F4EFE5] font-heading font-bold text-xs hover:bg-[#722f1c]"
                >
                  Return to Worker
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </ManagerShell>
  );
}

export default function ManagerSessionReviewPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F4EFE5]" aria-busy="true" />}>
      <ManagerSessionReviewContent />
    </Suspense>
  );
}
