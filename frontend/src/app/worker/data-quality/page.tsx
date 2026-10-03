'use client';

import React, { useState, useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import WorkerShell from '@/components/layout/WorkerShell';
import { useWorkflowStore } from '@/store/workflow-store';

export default function WorkerDataQualityPage() {
  const router = useRouter();
  const { dqIssues, resolveDqIssue, unresolveDqIssue, acceptAllRecommendedFixes } = useWorkflowStore();

  const [severityFilter, setSeverityFilter] = useState<'all' | 'critical' | 'warning' | 'info'>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('All Categories');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedIssueId, setExpandedIssueId] = useState<number | null>(1);

  // Dynamic counts
  const totalIssues = dqIssues.length;
  const criticalCount = dqIssues.filter((i) => i.severity === 'critical').length;
  const warningCount = dqIssues.filter((i) => i.severity === 'warning').length;
  const infoCount = dqIssues.filter((i) => i.severity === 'info').length;
  const unresolvedCount = dqIssues.filter((i) => i.status === 'pending').length;
  const resolvedCount = dqIssues.filter((i) => i.status === 'resolved').length;

  const filteredIssues = useMemo(() => {
    return dqIssues.filter((issue) => {
      const matchesSeverity = severityFilter === 'all' || issue.severity === severityFilter;
      const matchesCategory =
        categoryFilter === 'All Categories' || issue.category === categoryFilter;
      const matchesSearch =
        issue.title.toLowerCase().includes(searchQuery.toLowerCase().trim()) ||
        issue.description.toLowerCase().includes(searchQuery.toLowerCase().trim());
      return matchesSeverity && matchesCategory && matchesSearch;
    });
  }, [dqIssues, severityFilter, categoryFilter, searchQuery]);

  return (
    <WorkerShell>
      <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto pb-12">
        {/* Header & Governance Banner */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-1.5 text-[#8B9490] font-tag text-xs">
            <Link href="/worker/dashboard" className="hover:text-[#121C18]">
              SOVIA Hub
            </Link>
            <span className="material-symbols-outlined text-[13px]">chevron_right</span>
            <span>Pipeline Ingestion</span>
            <span className="material-symbols-outlined text-[13px]">chevron_right</span>
            <span className="text-[#121C18] font-semibold">Data Quality Review</span>
          </div>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mt-1">
            <div>
              <h1 className="font-heading text-2xl sm:text-3xl font-bold text-[#121C18] tracking-tight">
                Data Quality Review
              </h1>
              <p className="font-sans text-sm text-[#4A5550] max-w-3xl mt-1">
                Human-in-the-loop validation of actuarial anomalies, range violations, and field syntax before transformation.
              </p>
            </div>
            <div className="flex items-center gap-2 self-start md:self-auto bg-[#EBE5D9] px-3.5 py-1.5 rounded-lg border border-[#D5CEBF]">
              <span className="material-symbols-outlined text-[18px] text-[#0E3B28]">verified_user</span>
              <span className="font-tag text-xs text-[#0E3B28] font-bold">
                Data Quality Agent / Active
              </span>
            </div>
          </div>
        </div>

        {/* 4 Dynamic Summary Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[#EBE5D9] p-4 rounded-lg border border-[#D5CEBF] flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-tag text-xs uppercase tracking-wider text-[#8B9490] font-semibold">
                Total Flagged
              </span>
              <span className="material-symbols-outlined text-[20px] text-[#8B9490]">flag</span>
            </div>
            <div className="my-2">
              <span className="font-heading text-3xl font-bold text-[#121C18] leading-none">
                {totalIssues}
              </span>
            </div>
            <span className="font-sans text-xs text-[#4A5550]">842 records scanned</span>
          </div>

          <div className="bg-[#EBE5D9] p-4 rounded-lg border border-[#D5CEBF] flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-tag text-xs uppercase tracking-wider text-[#8C3B24] font-bold">
                Critical Anomalies
              </span>
              <span className="material-symbols-outlined text-[20px] text-[#8C3B24]">gpp_maybe</span>
            </div>
            <div className="my-2">
              <span className="font-heading text-3xl font-bold text-[#8C3B24] leading-none">
                {criticalCount}
              </span>
            </div>
            <span className="font-sans text-xs text-[#8C3B24]">Blocks pipeline · Individual review</span>
          </div>

          <div className="bg-[#EBE5D9] p-4 rounded-lg border border-[#D5CEBF] flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-tag text-xs uppercase tracking-wider text-[#B87A1E] font-bold">
                Warnings
              </span>
              <span className="material-symbols-outlined text-[20px] text-[#B87A1E]">warning_amber</span>
            </div>
            <div className="my-2">
              <span className="font-heading text-3xl font-bold text-[#B87A1E] leading-none">
                {warningCount}
              </span>
            </div>
            <span className="font-sans text-xs text-[#4A5550]">Format &amp; range anomalies</span>
          </div>

          <div className="bg-[#EBE5D9] p-4 rounded-lg border border-[#D5CEBF] flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-tag text-xs uppercase tracking-wider text-[#8B9490] font-semibold">
                Informational
              </span>
              <span className="material-symbols-outlined text-[20px] text-[#8B9490]">info</span>
            </div>
            <div className="my-2">
              <span className="font-heading text-3xl font-bold text-[#4A5550] leading-none">
                {infoCount}
              </span>
            </div>
            <span className="font-sans text-xs text-[#4A5550]">Minor syntax &amp; casing notes</span>
          </div>
        </div>

        {/* Filter and Controls Bar */}
        <div className="bg-[#EBE5D9] p-3 rounded-lg border border-[#D5CEBF] flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              type="button"
              onClick={() => setSeverityFilter('all')}
              className={`px-3 py-1.5 rounded-full font-tag text-xs font-semibold transition-colors cursor-pointer ${
                severityFilter === 'all'
                  ? 'bg-[#00C878] text-[#0E3B28] border border-[#00C878]'
                  : 'bg-[#F4EFE5] text-[#4A5550] border border-[#D5CEBF] hover:bg-[#EBE5D9]'
              }`}
            >
              All Issues ({totalIssues})
            </button>
            <button
              type="button"
              onClick={() => setSeverityFilter('critical')}
              className={`px-3 py-1.5 rounded-full font-tag text-xs font-bold transition-colors cursor-pointer ${
                severityFilter === 'critical'
                  ? 'bg-[#8C3B24] text-[#F4EFE5] border border-[#8C3B24]'
                  : 'bg-[#F4EFE5] text-[#8C3B24] border border-[#D5CEBF] hover:bg-[#FBEBE8]'
              }`}
            >
              Critical ({criticalCount})
            </button>
            <button
              type="button"
              onClick={() => setSeverityFilter('warning')}
              className={`px-3 py-1.5 rounded-full font-tag text-xs font-semibold transition-colors cursor-pointer ${
                severityFilter === 'warning'
                  ? 'bg-[#B87A1E] text-[#F4EFE5] border border-[#B87A1E]'
                  : 'bg-[#F4EFE5] text-[#B87A1E] border border-[#D5CEBF] hover:bg-[#F7ECC8]'
              }`}
            >
              Warnings ({warningCount})
            </button>
            <button
              type="button"
              onClick={() => setSeverityFilter('info')}
              className={`px-3 py-1.5 rounded-full font-tag text-xs font-semibold transition-colors cursor-pointer ${
                severityFilter === 'info'
                  ? 'bg-[#4A5550] text-[#F4EFE5] border border-[#4A5550]'
                  : 'bg-[#F4EFE5] text-[#4A5550] border border-[#D5CEBF] hover:bg-[#EBE5D9]'
              }`}
            >
              Informational ({infoCount})
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="relative">
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="bg-[#F4EFE5] border border-[#D5CEBF] text-[#121C18] font-tag text-xs rounded-lg pl-3 pr-8 py-1.5 outline-none cursor-pointer"
              >
                <option value="All Categories">All Categories</option>
                <option value="Negative/Impossible Values">Negative/Impossible Values</option>
                <option value="Cross-Field Inconsistencies">Cross-Field Inconsistencies</option>
                <option value="Inconsistent Values">Inconsistent Values</option>
                <option value="Outliers">Outliers</option>
                <option value="Invalid Formats">Invalid Formats</option>
              </select>
              <span className="material-symbols-outlined pointer-events-none absolute right-2 top-1.5 text-[18px] text-[#8B9490]">
                expand_more
              </span>
            </div>

            <div className="relative flex items-center min-w-[220px]">
              <span className="material-symbols-outlined text-[#8B9490] text-[18px] absolute left-2.5">
                search
              </span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter issues..."
                className="w-full bg-[#F4EFE5] border border-[#D5CEBF] text-[#121C18] placeholder-[#8B9490] text-xs rounded-lg pl-8 pr-3 py-1.5 outline-none focus:border-[#00C878]"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 text-[#8B9490] hover:text-[#121C18]"
                >
                  <span className="material-symbols-outlined text-[14px]">close</span>
                </button>
              )}
            </div>

            <div className="font-tag text-xs text-[#4A5550] bg-[#E5DEC9] px-3 py-1.5 rounded-lg border border-[#D5CEBF] whitespace-nowrap">
              <span className="font-bold text-[#8C3B24]">Unresolved ({unresolvedCount})</span> ·{' '}
              <span className="text-[#0E3B28] font-semibold">Resolved ({resolvedCount})</span>
            </div>
          </div>
        </div>

        {/* Issue Cards Stack */}
        <div className="flex flex-col gap-3">
          {filteredIssues.length === 0 ? (
            <div className="p-10 rounded-lg bg-[#EBE5D9] border border-[#D5CEBF] text-center text-sm text-[#8B9490]">
              <span className="material-symbols-outlined text-[32px] mb-1">done_all</span>
              <p className="font-heading font-semibold text-[#121C18]">No issues match the selected filter.</p>
              <p className="text-xs text-[#4A5550] mt-1">Try switching severity or category filters.</p>
            </div>
          ) : (
            filteredIssues.map((issue) => {
              const isExpanded = expandedIssueId === issue.id;
              const isCritical = issue.severity === 'critical';
              const isWarning = issue.severity === 'warning';
              const isResolved = issue.status === 'resolved';

              return (
                <div
                  key={issue.id}
                  className="bg-[#F4EFE5] rounded-lg border border-[#D5CEBF] overflow-hidden flex flex-col"
                >
                  <div
                    onClick={() => setExpandedIssueId(isExpanded ? null : issue.id)}
                    className={`p-4 flex items-center justify-between cursor-pointer transition-colors ${
                      isExpanded ? 'bg-[#EBE5D9]' : 'hover:bg-[#EBE5D9]'
                    }`}
                  >
                    <div className="flex items-center gap-3 flex-wrap">
                      <span
                        className={`px-2.5 py-0.5 rounded-full font-tag text-[10px] font-bold uppercase tracking-wider ${
                          isCritical
                            ? 'bg-[#8C3B24] text-[#F4EFE5]'
                            : isWarning
                            ? 'bg-[#F7ECC8] text-[#B87A1E] border border-[#B87A1E]'
                            : 'bg-[#E5DEC9] text-[#4A5550] border border-[#D5CEBF]'
                        }`}
                      >
                        {issue.severity}
                      </span>
                      <span className="font-heading font-bold text-sm text-[#121C18]">
                        {issue.title}
                      </span>
                      <span className="font-tag text-xs text-[#8B9490] bg-[#E5DEC9] px-2 py-0.5 rounded">
                        {issue.affectedRows}
                      </span>
                    </div>

                    <div className="flex items-center gap-3">
                      {isResolved ? (
                        <span className="font-tag text-xs text-[#0E3B28] font-bold bg-[#D1F2DE] px-2.5 py-0.5 rounded-full border border-[#7FE3B0] flex items-center gap-1">
                          <span className="material-symbols-outlined text-[14px]">check</span>
                          Resolved
                        </span>
                      ) : (
                        <span className="font-tag text-xs text-[#B87A1E] bg-[#F7ECC8] px-2.5 py-0.5 rounded border border-[#B87A1E] font-medium">
                          Pending Review
                        </span>
                      )}
                      <span className="material-symbols-outlined text-[#8B9490] text-[20px]">
                        {isExpanded ? 'expand_less' : 'expand_more'}
                      </span>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="p-4 pt-2 bg-[#F4EFE5] border-t border-[#D5CEBF] flex flex-col gap-3">
                      <p className="font-sans text-xs text-[#4A5550] leading-relaxed">
                        {issue.description}
                      </p>

                      <div className="p-3 rounded bg-[#EBE5D9] border border-[#D5CEBF] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                        <div>
                          <span className="font-tag text-[11px] uppercase tracking-wider text-[#8B9490] font-bold block mb-0.5">
                            Suggested Remediation:
                          </span>
                          <span className="font-medium text-[#121C18]">{issue.suggestedFix}</span>
                        </div>

                        {!isResolved ? (
                          <button
                            type="button"
                            onClick={() => resolveDqIssue(issue.id)}
                            className="px-4 py-1.5 rounded-full bg-[#00C878] hover:bg-[#00b56c] text-[#0E3B28] font-heading font-bold text-xs flex items-center gap-1 shrink-0 cursor-pointer shadow-none"
                          >
                            <span className="material-symbols-outlined text-[15px]">build</span>
                            Apply Fix
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => unresolveDqIssue(issue.id)}
                            className="px-3 py-1 rounded-full border border-[#D5CEBF] bg-[#F4EFE5] hover:bg-[#EBE5D9] text-[#8C3B24] font-heading text-xs flex items-center gap-1 shrink-0 cursor-pointer"
                          >
                            <span className="material-symbols-outlined text-[14px]">undo</span>
                            Re-open Issue
                          </button>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Governance Footer Bar */}
        <div className="bg-[#EBE5D9] p-4 rounded-lg border border-[#D5CEBF] flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <button
              type="button"
              onClick={acceptAllRecommendedFixes}
              className="px-4 py-2 rounded-full font-tag text-xs font-bold text-[#0E3B28] bg-[#F4EFE5] border border-[#D5CEBF] hover:bg-[#E5DEC9] transition-colors cursor-pointer"
            >
              Accept all recommended fixes
            </button>
            <p className="font-sans text-xs text-[#4A5550]">
              Applies to non-critical warnings and informational items. Critical issues require individual human sign-off.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-end sm:items-center gap-4 w-full md:w-auto justify-end">
            <span className="font-tag text-[11px] text-[#8B9490] text-right">
              All resolutions are cryptographically logged to the tamper-evident session audit trail.
            </span>
            <button
              type="button"
              onClick={() => router.push('/worker/transformation')}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full font-heading text-xs font-bold bg-[#00C878] text-[#0E3B28] hover:bg-[#00b56c] transition-colors cursor-pointer whitespace-nowrap shadow-none"
            >
              <span>Continue to Transformation</span>
              <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>
    </WorkerShell>
  );
}
