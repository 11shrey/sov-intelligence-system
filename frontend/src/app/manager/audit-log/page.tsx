'use client';

import React, { useState, useMemo } from 'react';
import ManagerShell from '@/components/layout/ManagerShell';
import { useWorkflowStore } from '@/store/workflow-store';
import { downloadCsv } from '@/lib/download';

interface OrgAuditItem {
  id: string;
  time: string;
  date: string;
  actor: string;
  actorRole: string;
  actorType: 'manager' | 'worker' | 'ai';
  action: string;
  targetFile: string;
  targetSub: string;
  outcome: 'Approved' | 'Awaiting Review' | 'Flagged' | 'Accepted' | 'Returned' | 'Edited';
  outcomeColor: 'green' | 'amber' | 'rust';
  hash: string;
  aiRec?: { title: string; match: string; mono: string; desc: string };
  humanGate?: { title: string; badge: string; name: string; role: string; desc: string };
  ruleChange?: { title: string; badge: string; target: string; type: string; desc: string };
  nonce: string;
}

const STATIC_ORG_EVENTS: OrgAuditItem[] = [
  {
    id: 'evt-1',
    time: '10:45 AM',
    date: 'Oct 2, 2026',
    actor: 'S. Reynolds',
    actorRole: 'Risk Lead',
    actorType: 'manager',
    action: 'Approved transformation',
    targetFile: 'Property_SOV_Jan.xlsx',
    targetSub: 'SOV-2026-1042',
    outcome: 'Approved',
    outcomeColor: 'green',
    hash: 'sha256:7f99b0c2...e81a',
    aiRec: {
      title: 'Original AI Recommendation',
      match: '96% Match',
      mono: 'Map Yr Built → Year Built',
      desc: "Source field syntax and observed discrete values matched the standardized schema token 'YEAR_BUILT_ISO' with zero missing indices.",
    },
    humanGate: {
      title: 'Human Decision Gate',
      badge: 'Accepted',
      name: 'S. Reynolds',
      role: 'Manager, Risk Underwriting',
      desc: 'Validated historical compliance thresholds. Manual confirmation verified against policy ledger ref #UW-48992.',
    },
    ruleChange: {
      title: 'Resulting Rule Change',
      badge: 'Active',
      target: 'Year Built',
      type: 'INTEGER (YYYY)',
      desc: 'Deterministic batch clean applied across 1,284 cell coordinate pairs. Checksum verified.',
    },
    nonce: '0x93FA910B',
  },
  {
    id: 'evt-2',
    time: '10:42 AM',
    date: 'Oct 2, 2026',
    actor: 'Aarav Sharma',
    actorRole: 'Risk Ops Worker',
    actorType: 'worker',
    action: 'Submitted session for review',
    targetFile: 'Property_SOV_Jan.xlsx',
    targetSub: 'SOV-2026-1042',
    outcome: 'Awaiting Review',
    outcomeColor: 'amber',
    hash: 'sha256:8f4a99c2...4110',
    aiRec: {
      title: 'Automated Pre-submission Check',
      match: '100% Passed',
      mono: 'Validation Gate: Ready for Dual Authorization',
      desc: 'All 17 fields mapped, 5 transformations applied, zero unmitigated critical DQ alerts remaining.',
    },
    humanGate: {
      title: 'Worker Sign-off',
      badge: 'Submitted',
      name: 'Aarav Sharma',
      role: 'Risk Ops Worker (AS-90412)',
      desc: 'Session completed with all primary commercial real estate property schedules mapped to canonical schema.',
    },
    ruleChange: {
      title: 'Queue Dispatch',
      badge: 'Queued',
      target: 'Session SOV-2026-1042',
      type: 'L4 DUAL AUTHORIZATION',
      desc: 'Dispatched to Manager S. Reynolds review backlog. Turnaround SLA timer initiated.',
    },
    nonce: '0x10B49F88',
  },
  {
    id: 'evt-3',
    time: '10:24 AM',
    date: 'Oct 2, 2026',
    actor: 'Data Quality Agent',
    actorRole: 'SOVIA Core AI',
    actorType: 'ai',
    action: 'Detected 3 data-quality issues',
    targetFile: 'Field: "Yr Built"',
    targetSub: 'Property_SOV_Jan.xlsx',
    outcome: 'Flagged',
    outcomeColor: 'amber',
    hash: 'sha256:3c9d81fe...7710',
    aiRec: {
      title: 'Heuristic Anomaly Flagging',
      match: 'Rule #DQ-204',
      mono: 'Negative Replacement Cost & Inconsistent Postal',
      desc: 'Identified negative cost basis in Bldg_Repl_Cost_USD and postal code state misalignment (60601 with state IN).',
    },
    humanGate: {
      title: 'System Quarantine',
      badge: 'Intercepted',
      name: 'Data Quality Agent v2.4',
      role: 'Automated Integrity Watchdog',
      desc: 'Quarantined 3 records from final output until explicit human reconciliation.',
    },
    ruleChange: {
      title: 'Diagnostic Alert',
      badge: 'Flagged',
      target: 'DQ Issue Backlog',
      type: 'EXCEPTION_QUEUE',
      desc: 'Created remediation tasks in worker data quality dashboard.',
    },
    nonce: '0x44F019AB',
  },
  {
    id: 'evt-4',
    time: '10:18 AM',
    date: 'Oct 2, 2026',
    actor: 'Schema Agent',
    actorRole: 'SOVIA Core AI',
    actorType: 'ai',
    action: 'Mapped 17/17 schema fields',
    targetFile: 'Field: "Year Built"',
    targetSub: 'Session: SOV-2026-1042',
    outcome: 'Accepted',
    outcomeColor: 'green',
    hash: 'sha256:5d88c140...902a',
    aiRec: {
      title: 'Embeddings Cosine Similarity',
      match: '94% Avg',
      mono: 'SOV Schedule → CRE Canonical 17-field Model',
      desc: 'High confidence match on Bldg_Repl_Cost, Const_Type, Occupancy_Class, TIV_Total, and Postal coordinates.',
    },
    humanGate: {
      title: 'Batch Worker Auto-Pass',
      badge: 'Auto-Matched',
      name: 'Schema Agent L2',
      role: 'Automated Mapping Classifier',
      desc: '14 high confidence (>90%) fields auto-accepted per organization compliance baseline.',
    },
    ruleChange: {
      title: 'Schema Normalization Matrix',
      badge: 'Locked',
      target: '17 Target Fields',
      type: 'SCHEMA_NORMALIZATION',
      desc: 'Established column projection indices for downstream staging tables.',
    },
    nonce: '0x88BA12C0',
  },
  {
    id: 'evt-5',
    time: '09:56 AM',
    date: 'Oct 2, 2026',
    actor: 'S. Reynolds',
    actorRole: 'Risk Lead',
    actorType: 'manager',
    action: 'Returned submission with remarks',
    targetFile: 'MetroAssets_SOV.xlsx',
    targetSub: 'Variance > 12% Cost Basis',
    outcome: 'Returned',
    outcomeColor: 'rust',
    hash: 'sha256:2f11a87b...0911',
    aiRec: {
      title: 'Actuarial Variance Trigger',
      match: 'Discrepancy',
      mono: 'TIV_Total Variance > 12% Threshold',
      desc: 'Aggregate insured valuation diverged significantly from prior submission benchmark #UW-2025-Q4.',
    },
    humanGate: {
      title: 'Manager Dual Authorization Check',
      badge: 'Returned',
      name: 'S. Reynolds',
      role: 'Manager, Risk Underwriting',
      desc: 'Returned to Kabir Singh with remediation mandate: Verify asset tier 2 appraisal notes before sign-off.',
    },
    ruleChange: {
      title: 'Workflow State Regression',
      badge: 'Rework Required',
      target: 'Session SOV-2026-1038',
      type: 'REMEDIATION_CYCLE',
      desc: 'Session unlocked for worker edit; re-submission required prior to L4 authorization.',
    },
    nonce: '0x33A0B11D',
  },
  {
    id: 'evt-6',
    time: '09:18 AM',
    date: 'Oct 2, 2026',
    actor: 'Riya Mehta',
    actorRole: 'Risk Analyst',
    actorType: 'worker',
    action: 'Remapped field with manual override',
    targetFile: 'Const_Type → Construction Type',
    targetSub: 'Session: SOV-2026-0988',
    outcome: 'Edited',
    outcomeColor: 'amber',
    hash: 'sha256:9a410b3c...e400',
    aiRec: {
      title: 'Original Ambiguous Proposal',
      match: '64% Match',
      mono: 'Const_Type → Occupancy Type',
      desc: 'Confidence below 80% threshold due to mixed alphanumeric broker formatting.',
    },
    humanGate: {
      title: 'Worker Manual Override',
      badge: 'Modified',
      name: 'Riya Mehta',
      role: 'Risk Analyst (RM-20941)',
      desc: 'Overrode automated recommendation; assigned canonical target Construction Type per contract appendix B.',
    },
    ruleChange: {
      title: 'Mapping Override Hash',
      badge: 'Persisted',
      target: 'Const_Type',
      type: 'MANUAL_OVERRIDE',
      desc: 'Target bound to Construction Class with strict enumerated value lookup.',
    },
    nonce: '0x77EC4190',
  },
];

export default function ManagerAuditLogPage() {
  const { auditEvents } = useWorkflowStore();

  const [viewState, setViewState] = useState<'live' | 'empty' | 'skeleton'>('live');
  const [selectedActor, setSelectedActor] = useState<'all' | 'ai' | 'worker' | 'manager'>('all');
  const [userFilter, setUserFilter] = useState('All Users');
  const [actionFilter, setActionFilter] = useState('All Actions');
  const [dateFilter, setDateFilter] = useState('Last 7 days');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({ 'evt-1': true });
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  const toggleRow = (id: string) => {
    setExpandedRows((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  // Convert any newly added store events to match OrgAuditItem shape
  const mergedEvents: OrgAuditItem[] = useMemo(() => {
    const dynamicItems: OrgAuditItem[] = auditEvents
      .filter((ae) => !STATIC_ORG_EVENTS.some((se) => se.id === ae.id))
      .map((ae) => {
        let outcome: OrgAuditItem['outcome'] = 'Accepted';
        let outcomeColor: OrgAuditItem['outcomeColor'] = 'green';
        if (ae.status === 'approved') {
          outcome = 'Approved';
          outcomeColor = 'green';
        } else if (ae.status === 'awaiting') {
          outcome = 'Awaiting Review';
          outcomeColor = 'amber';
        } else if (ae.status === 'returned') {
          outcome = 'Returned';
          outcomeColor = 'rust';
        } else if (ae.status === 'flagged') {
          outcome = 'Flagged';
          outcomeColor = 'amber';
        }

        return {
          id: ae.id,
          time: ae.timestamp.replace('Today ', ''),
          date: ae.date || 'Oct 2, 2026',
          actor: ae.actor,
          actorRole: ae.actorTitle || (ae.actorType === 'manager' ? 'Risk Lead' : 'Risk Worker'),
          actorType: ae.actorType,
          action: ae.action,
          targetFile: ae.sessionFile || ae.targetScope,
          targetSub: ae.sessionId || 'SOV-2026-1042',
          outcome,
          outcomeColor,
          hash: ae.evidenceHash || 'sha256:7f99b0c2...e81a',
          aiRec: ae.aiRecommendation
            ? {
                title: 'Original AI Recommendation',
                match: '96% Match',
                mono: ae.aiRecommendation,
                desc: 'Deterministic heuristics verified schema alignment.',
              }
            : undefined,
          humanGate: ae.humanDecision
            ? {
                title: 'Human Decision Gate',
                badge: outcome,
                name: ae.actor,
                role: ae.actorTitle || 'Enterprise Risk Role',
                desc: ae.humanDecision,
              }
            : undefined,
          ruleChange: ae.resultingRule
            ? {
                title: 'Resulting Rule Change',
                badge: 'Active',
                target: ae.targetScope,
                type: 'LEDGER_VERIFIED',
                desc: ae.resultingRule,
              }
            : undefined,
          nonce: ae.nonce || '0x93FA910B',
        };
      });

    return [...dynamicItems, ...STATIC_ORG_EVENTS];
  }, [auditEvents]);

  // Filtered rows
  const filteredEvents = useMemo(() => {
    return mergedEvents.filter((item) => {
      // Actor pill filter
      if (selectedActor !== 'all' && item.actorType !== selectedActor) return false;

      // User filter
      if (userFilter !== 'All Users') {
        if (!item.actor.toLowerCase().includes(userFilter.toLowerCase())) return false;
      }

      // Action filter
      if (actionFilter !== 'All Actions') {
        if (!item.action.toLowerCase().includes(actionFilter.toLowerCase())) return false;
      }

      // Search query
      if (searchQuery.trim() !== '') {
        const q = searchQuery.toLowerCase();
        const matchesHash = item.hash.toLowerCase().includes(q);
        const matchesFile = item.targetFile.toLowerCase().includes(q);
        const matchesActor = item.actor.toLowerCase().includes(q);
        const matchesAction = item.action.toLowerCase().includes(q);
        if (!matchesHash && !matchesFile && !matchesActor && !matchesAction) return false;
      }

      return true;
    });
  }, [mergedEvents, selectedActor, userFilter, actionFilter, searchQuery]);

  const handleExport = () => {
    downloadCsv(
      'SOVIA_Organization_Audit_Log.csv',
      ['Event ID', 'Date', 'Time', 'Actor', 'Actor Type', 'Action', 'Target File', 'Outcome', 'Evidence Hash'],
      filteredEvents.map((item) => [
        item.id,
        item.date,
        item.time,
        item.actor,
        item.actorType,
        item.action,
        item.targetFile,
        item.outcome,
        item.hash,
      ]),
    );
    setExportNotice(`Exported ${filteredEvents.length} ledger events to CSV.`);
    setTimeout(() => {
      setExportNotice(null);
    }, 4000);
  };

  return (
    <ManagerShell>
      <div className="flex flex-col w-full p-6 gap-5 text-[#121C18]">
        {/* PAGE HEADER & CONTROLS */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#D5CEBF] pb-4">
          <div className="flex flex-col gap-0.5">
            <div className="flex items-center gap-2">
              <h1 className="font-headline-lg text-[24px] leading-8 font-bold text-[#121C18] tracking-tight">
                Org Audit Log
              </h1>
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-label-sm uppercase tracking-wider bg-[#D1F2DE] text-[#0E3B28] font-bold border border-[#00C878]/30">
                <span className="w-1.5 h-1.5 rounded-full bg-[#00C878]"></span>
                L4 Ledger
              </span>
            </div>
            <p className="font-body-md text-[13px] text-[#4A5550]">
              Organization-wide immutable record of AI, Worker, and Manager actions.
            </p>
          </div>

          {/* Actions & View Switcher */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Dev / QA State Switcher */}
            <div className="inline-flex p-0.5 bg-[#EBE5D9] rounded-lg border border-[#D5CEBF] text-[11px] font-label-sm">
              <button
                type="button"
                className={`px-2.5 py-1 rounded transition-all cursor-pointer ${
                  viewState === 'live'
                    ? 'bg-[#F4EFE5] text-[#121C18] font-semibold'
                    : 'text-[#4A5550] hover:text-[#121C18]'
                }`}
                onClick={() => setViewState('live')}
              >
                Live Log
              </button>
              <button
                type="button"
                className={`px-2.5 py-1 rounded transition-all cursor-pointer ${
                  viewState === 'empty'
                    ? 'bg-[#F4EFE5] text-[#121C18] font-semibold'
                    : 'text-[#4A5550] hover:text-[#121C18]'
                }`}
                onClick={() => setViewState('empty')}
              >
                Empty State
              </button>
              <button
                type="button"
                className={`px-2.5 py-1 rounded transition-all cursor-pointer ${
                  viewState === 'skeleton'
                    ? 'bg-[#F4EFE5] text-[#121C18] font-semibold'
                    : 'text-[#4A5550] hover:text-[#121C18]'
                }`}
                onClick={() => setViewState('skeleton')}
              >
                Skeleton Loading
              </button>
            </div>

            {/* Export Button */}
            <button
              type="button"
              onClick={handleExport}
              className="inline-flex items-center gap-1.5 border border-[#3F6B52] text-[#3F6B52] bg-[#F4EFE5] hover:bg-[#EBE5D9] px-3.5 py-1.5 rounded-lg text-[12px] font-label-sm font-semibold tracking-wide transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">file_download</span>
              Export Log ⤓
            </button>
          </div>
        </div>

        {/* Export Notification Toast */}
        {exportNotice && (
          <div className="p-3 bg-[#D1F2DE] border border-[#00C878] rounded text-xs text-[#0E3B28] flex items-center justify-between font-label-sm font-semibold">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">verified</span>
              <span>{exportNotice}</span>
            </div>
            <button
              type="button"
              onClick={() => setExportNotice(null)}
              className="text-[#0E3B28] font-bold text-xs"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* FILTER TOOLBAR */}
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-2 bg-[#EBE5D9] p-2 rounded-lg border border-[#D5CEBF]">
          {/* Actor Pill Group */}
          <div className="flex flex-wrap items-center gap-1">
            <button
              type="button"
              onClick={() => setSelectedActor('all')}
              className={`px-3 py-1 rounded text-[12px] font-label-sm font-semibold transition-colors cursor-pointer ${
                selectedActor === 'all'
                  ? 'bg-[#00C878] text-[#0E3B28]'
                  : 'bg-[#F4EFE5] border border-[#D5CEBF] text-[#4A5550] hover:text-[#121C18] hover:bg-[#EBE5D9]'
              }`}
            >
              All (142)
            </button>
            <button
              type="button"
              onClick={() => setSelectedActor('ai')}
              className={`px-3 py-1 rounded text-[12px] font-label-sm font-medium transition-colors cursor-pointer ${
                selectedActor === 'ai'
                  ? 'bg-[#00C878] text-[#0E3B28] font-semibold'
                  : 'bg-[#F4EFE5] border border-[#D5CEBF] text-[#4A5550] hover:text-[#121C18] hover:bg-[#EBE5D9]'
              }`}
            >
              AI Agents (68)
            </button>
            <button
              type="button"
              onClick={() => setSelectedActor('worker')}
              className={`px-3 py-1 rounded text-[12px] font-label-sm font-medium transition-colors cursor-pointer ${
                selectedActor === 'worker'
                  ? 'bg-[#00C878] text-[#0E3B28] font-semibold'
                  : 'bg-[#F4EFE5] border border-[#D5CEBF] text-[#4A5550] hover:text-[#121C18] hover:bg-[#EBE5D9]'
              }`}
            >
              Workers (48)
            </button>
            <button
              type="button"
              onClick={() => setSelectedActor('manager')}
              className={`px-3 py-1 rounded text-[12px] font-label-sm font-medium transition-colors cursor-pointer ${
                selectedActor === 'manager'
                  ? 'bg-[#00C878] text-[#0E3B28] font-semibold'
                  : 'bg-[#F4EFE5] border border-[#D5CEBF] text-[#4A5550] hover:text-[#121C18] hover:bg-[#EBE5D9]'
              }`}
            >
              Managers (26)
            </button>
          </div>

          {/* Dropdowns & Search */}
          <div className="flex flex-wrap items-center gap-2">
            {/* User Dropdown */}
            <div className="relative inline-block">
              <select
                value={userFilter}
                onChange={(e) => setUserFilter(e.target.value)}
                className="appearance-none bg-[#F4EFE5] border border-[#D5CEBF] text-[#121C18] text-[12px] font-body-md py-1 pl-2.5 pr-7 rounded focus:outline-none cursor-pointer"
              >
                <option value="All Users">User: All Users</option>
                <option value="S. Reynolds">S. Reynolds (Manager)</option>
                <option value="Aarav Sharma">Aarav Sharma (Worker)</option>
                <option value="Riya Mehta">Riya Mehta (Worker)</option>
                <option value="Kabir Singh">Kabir Singh (Worker)</option>
              </select>
              <span className="material-symbols-outlined text-[16px] text-[#4A5550] pointer-events-none absolute right-1.5 top-1/2 -translate-y-1/2">
                expand_more
              </span>
            </div>

            {/* Action Dropdown */}
            <div className="relative inline-block">
              <select
                value={actionFilter}
                onChange={(e) => setActionFilter(e.target.value)}
                className="appearance-none bg-[#F4EFE5] border border-[#D5CEBF] text-[#121C18] text-[12px] font-body-md py-1 pl-2.5 pr-7 rounded focus:outline-none cursor-pointer"
              >
                <option value="All Actions">Action: All Actions</option>
                <option value="Approved">Approved transformation</option>
                <option value="Submitted">Submitted submission</option>
                <option value="Detected">Detected issues</option>
                <option value="Mapped">Mapped schema</option>
                <option value="Returned">Returned submission</option>
                <option value="override">Manual override</option>
              </select>
              <span className="material-symbols-outlined text-[16px] text-[#4A5550] pointer-events-none absolute right-1.5 top-1/2 -translate-y-1/2">
                expand_more
              </span>
            </div>

            {/* Date Dropdown */}
            <div className="relative inline-block">
              <select
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="appearance-none bg-[#F4EFE5] border border-[#D5CEBF] text-[#121C18] text-[12px] font-body-md py-1 pl-2.5 pr-7 rounded focus:outline-none cursor-pointer"
              >
                <option value="Last 7 days">Date: Last 7 days</option>
                <option value="Today">Today (Oct 2, 2026)</option>
                <option value="Last 30 days">Last 30 days</option>
                <option value="Custom">Custom range...</option>
              </select>
              <span className="material-symbols-outlined text-[16px] text-[#4A5550] pointer-events-none absolute right-1.5 top-1/2 -translate-y-1/2">
                calendar_today
              </span>
            </div>

            {/* Compact Search input */}
            <div className="relative flex-1 sm:w-56">
              <span className="material-symbols-outlined text-[16px] text-[#8B9490] absolute left-2 top-1/2 -translate-y-1/2 pointer-events-none">
                search
              </span>
              <input
                className="w-full bg-[#F4EFE5] border border-[#D5CEBF] text-[12px] font-body-md pl-7 pr-2 py-1 rounded placeholder-[#8B9490] text-[#121C18] focus:outline-none"
                placeholder="Search hash, file, target..."
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* VIEW CONTAINER 1: LIVE LOG VIEW */}
        {viewState === 'live' && (
          <div className="flex flex-col w-full">
            <div className="w-full bg-[#F4EFE5] border border-[#D5CEBF] rounded-lg overflow-x-auto shadow-none">
              <table className="w-full text-left border-collapse min-w-[960px]">
                <thead>
                  <tr className="bg-[#E5DEC9] border-b border-[#D5CEBF] font-label-sm uppercase tracking-wider text-[11px] text-[#4A5550] h-9">
                    <th className="py-2 px-3 w-28 font-medium">Timestamp</th>
                    <th className="py-2 px-3 w-44 font-medium">Actor</th>
                    <th className="py-2 px-3 w-64 font-medium">Action</th>
                    <th className="py-2 px-3 w-56 font-medium">Target</th>
                    <th className="py-2 px-3 w-36 font-medium">Outcome</th>
                    <th className="py-2 px-3 w-20 text-right font-medium">Evidence</th>
                  </tr>
                </thead>
                <tbody className="font-body-md text-[13px] text-[#121C18]">
                  {filteredEvents.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-[#4A5550] font-body-md text-sm">
                        No audit events match current criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredEvents.map((item) => {
                      const isExpanded = !!expandedRows[item.id];
                      return (
                        <React.Fragment key={item.id}>
                          <tr
                            className={`h-11 border-b border-[#DFD9CC] transition-colors cursor-pointer ${
                              isExpanded ? 'bg-[#EBE5D9]/50' : 'hover:bg-[#EBE5D9]/40'
                            }`}
                            onClick={() => toggleRow(item.id)}
                          >
                            {/* Timestamp */}
                            <td className="py-2 px-3 align-middle whitespace-nowrap">
                              <span className="font-medium text-[#121C18]">{item.time}</span>
                              <span className="text-[11px] text-[#4A5550] block font-label-sm">
                                {item.date}
                              </span>
                            </td>

                            {/* Actor */}
                            <td className="py-2 px-3 align-middle">
                              <div className="flex items-center gap-1.5">
                                {item.actorType === 'manager' && (
                                  <span className="w-5 h-5 rounded flex items-center justify-center bg-[#0E3B28] text-white">
                                    <span className="material-symbols-outlined text-[13px]">shield_person</span>
                                  </span>
                                )}
                                {item.actorType === 'worker' && (
                                  <span className="w-5 h-5 rounded flex items-center justify-center bg-[#00C878] text-[#0E3B28]">
                                    <span className="material-symbols-outlined text-[13px]">person</span>
                                  </span>
                                )}
                                {item.actorType === 'ai' && (
                                  <span className="w-5 h-5 rounded flex items-center justify-center bg-[#0E3B28] text-[#00C878]">
                                    <span className="material-symbols-outlined text-[13px]">smart_toy</span>
                                  </span>
                                )}
                                <div className="flex flex-col">
                                  <span className="font-semibold text-[13px] leading-tight text-[#121C18]">
                                    {item.actor}
                                  </span>
                                  <span className="text-[10px] text-[#4A5550] font-label-sm uppercase">
                                    {item.actorRole}
                                  </span>
                                </div>
                              </div>
                            </td>

                            {/* Action */}
                            <td className="py-2 px-3 align-middle text-[#121C18] font-medium">
                              {item.action}
                            </td>

                            {/* Target */}
                            <td className="py-2 px-3 align-middle text-[12px]">
                              <span className="font-medium text-[#121C18] block truncate max-w-[210px]">
                                {item.targetFile}
                              </span>
                              <span
                                className={`text-[11px] font-label-sm ${
                                  item.outcome === 'Returned' ? 'text-[#8C3B24]' : 'text-[#8B9490]'
                                }`}
                              >
                                {item.targetSub}
                              </span>
                            </td>

                            {/* Outcome Badge */}
                            <td className="py-2 px-3 align-middle">
                              {item.outcomeColor === 'green' && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-label-sm font-bold bg-[#D1F2DE] text-[#0E3B28] border border-[#00C878]/30">
                                  {item.outcome}
                                </span>
                              )}
                              {item.outcomeColor === 'amber' && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-label-sm font-bold bg-[#F7ECC8] text-[#B87A1E] border border-[#B87A1E]/20">
                                  {item.outcome}
                                </span>
                              )}
                              {item.outcomeColor === 'rust' && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-label-sm font-bold bg-[#FBEBE8] text-[#8C3B24] border border-[#8C3B24]/30">
                                  {item.outcome}
                                </span>
                              )}
                            </td>

                            {/* Evidence Chevron */}
                            <td className="py-2 px-3 align-middle text-right">
                              <span
                                className={`material-symbols-outlined text-[18px] text-[#4A5550] transition-transform ${
                                  isExpanded ? 'rotate-180' : ''
                                }`}
                              >
                                expand_more
                              </span>
                            </td>
                          </tr>

                          {/* EXPANDED EVIDENCE DETAIL ROW */}
                          {isExpanded && (
                            <tr className="border-b border-[#D5CEBF] bg-[#EBE5D9]/80">
                              <td className="p-4" colSpan={6}>
                                <div className="flex flex-col gap-3 font-body-md text-[12px] bg-[#F4EFE5] border border-[#D5CEBF] rounded p-3.5">
                                  {/* Hash & Immutable Ledger Banner */}
                                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-2.5 border-b border-[#DFD9CC]">
                                    <div className="flex items-center gap-2">
                                      <span className="material-symbols-outlined text-[16px] text-[#006d3f]">
                                        verified
                                      </span>
                                      <span className="font-label-sm text-[11px] uppercase tracking-wider text-[#4A5550] font-bold">
                                        AUDIT EVENT EVIDENCE HASH:{' '}
                                        <span className="font-mono text-[#121C18] lowercase font-normal">
                                          {item.hash}
                                        </span>
                                      </span>
                                    </div>
                                    <span className="font-label-sm text-[10px] uppercase tracking-wider text-[#0E3B28] bg-[#C6EED7] px-2 py-0.5 rounded border border-[#00C878]/40 font-bold self-start sm:self-auto">
                                      IMMUTABLE RECORD · L4 VERIFIED
                                    </span>
                                  </div>

                                  {/* Structured 3-Column Evidence Grid */}
                                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                    {/* Block 1: AI Recommendation */}
                                    <div className="p-3 bg-[#EBE5D9] border border-[#D5CEBF] rounded flex flex-col gap-1.5">
                                      <div className="flex items-center justify-between">
                                        <span className="font-label-sm text-[11px] uppercase tracking-wide font-bold text-[#4A5550]">
                                          {item.aiRec?.title || 'Original AI Recommendation'}
                                        </span>
                                        <span className="px-1.5 py-0.2 rounded text-[10px] font-label-sm font-bold bg-[#D1F2DE] text-[#0E3B28]">
                                          {item.aiRec?.match || '96% Match'}
                                        </span>
                                      </div>
                                      <div className="font-mono text-[12px] text-[#121C18] font-semibold bg-[#F4EFE5] p-1.5 rounded border border-[#DFD9CC]">
                                        {item.aiRec?.mono || 'Field Normalization Rule'}
                                      </div>
                                      <p className="text-[11px] text-[#4A5550] leading-relaxed">
                                        {item.aiRec?.desc ||
                                          'Discrete tokens validated against ISO underwriting dictionary.'}
                                      </p>
                                    </div>

                                    {/* Block 2: Human Decision Gate */}
                                    <div className="p-3 bg-[#EBE5D9] border border-[#D5CEBF] rounded flex flex-col gap-1.5">
                                      <div className="flex items-center justify-between">
                                        <span className="font-label-sm text-[11px] uppercase tracking-wide font-bold text-[#4A5550]">
                                          {item.humanGate?.title || 'Human Decision Gate'}
                                        </span>
                                        <span className="px-1.5 py-0.2 rounded text-[10px] font-label-sm font-bold bg-[#D1F2DE] text-[#0E3B28]">
                                          {item.humanGate?.badge || item.outcome}
                                        </span>
                                      </div>
                                      <div className="text-[12px] text-[#121C18] font-medium bg-[#F4EFE5] p-1.5 rounded border border-[#DFD9CC] flex flex-col">
                                        <span className="font-semibold">
                                          {item.humanGate?.name || item.actor}
                                        </span>
                                        <span className="text-[10px] text-[#4A5550]">
                                          {item.humanGate?.role || item.actorRole}
                                        </span>
                                      </div>
                                      <p className="text-[11px] text-[#4A5550] leading-relaxed">
                                        {item.humanGate?.desc ||
                                          'Validated historical compliance thresholds. Manual confirmation verified against policy ledger.'}
                                      </p>
                                    </div>

                                    {/* Block 3: Resulting Execution */}
                                    <div className="p-3 bg-[#EBE5D9] border border-[#D5CEBF] rounded flex flex-col gap-1.5">
                                      <div className="flex items-center justify-between">
                                        <span className="font-label-sm text-[11px] uppercase tracking-wide font-bold text-[#4A5550]">
                                          {item.ruleChange?.title || 'Resulting Rule Change'}
                                        </span>
                                        <span className="px-1.5 py-0.2 rounded text-[10px] font-label-sm font-semibold bg-[#E5DEC9] text-[#121C18]">
                                          {item.ruleChange?.badge || 'Active'}
                                        </span>
                                      </div>
                                      <div className="text-[11px] text-[#121C18] bg-[#F4EFE5] p-1.5 rounded border border-[#DFD9CC] font-mono leading-tight">
                                        <div>
                                          Target:{' '}
                                          <span className="font-semibold">
                                            {item.ruleChange?.target || 'Canonical Target'}
                                          </span>
                                        </div>
                                        <div>
                                          Type:{' '}
                                          <span className="text-[#0E3B28]">
                                            {item.ruleChange?.type || 'VERIFIED_SCHEME'}
                                          </span>
                                        </div>
                                      </div>
                                      <p className="text-[11px] text-[#4A5550] leading-relaxed">
                                        {item.ruleChange?.desc ||
                                          'Deterministic batch clean applied across cell coordinate pairs. Checksum verified.'}
                                      </p>
                                    </div>
                                  </div>

                                  {/* Footer disclaimer / cryptographic seal */}
                                  <div className="flex items-center justify-between pt-1 text-[11px] text-[#8B9490] font-label-sm">
                                    <span>
                                      Cryptographically signed by SOVIA SecureLedger v3.14 · Hardware Security
                                      Module (HSM) verified
                                    </span>
                                    <span className="font-mono text-[10px] text-[#4A5550]">
                                      Nonce: {item.nonce}
                                    </span>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* TABLE FOOTER */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-2 pt-3 text-[12px] text-[#4A5550]">
              {/* Record Count */}
              <div className="flex items-center gap-2">
                <span className="font-body-md text-[#4A5550]">
                  Showing <span className="font-semibold text-[#121C18]">{filteredEvents.length}</span> of{' '}
                  <span className="font-semibold text-[#121C18]">142</span> immutable audit ledger records
                </span>
              </div>

              {/* Ledger Sync Indicator & Pagination */}
              <div className="flex items-center gap-4">
                <div className="inline-flex items-center gap-1.5 text-[11px] font-label-sm uppercase tracking-wide text-[#0E3B28]">
                  <span className="w-2 h-2 rounded-full bg-[#00C878]"></span>
                  <span>Ledger Synced · Verification Pass 100%</span>
                </div>

                {/* Pagination Controls */}
                <div className="inline-flex items-center gap-1 bg-[#EBE5D9] border border-[#D5CEBF] rounded p-0.5 font-label-sm text-[12px]">
                  <button
                    type="button"
                    className="px-2 py-0.5 rounded text-[#8B9490] cursor-not-allowed"
                    disabled
                  >
                    ‹
                  </button>
                  <span className="px-2 py-0.5 font-semibold text-[#121C18]">1 of 24</span>
                  <button
                    type="button"
                    className="px-2 py-0.5 rounded hover:bg-[#F4EFE5] text-[#121C18] transition-colors cursor-pointer"
                  >
                    ›
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* VIEW CONTAINER 2: EMPTY STATE */}
        {viewState === 'empty' && (
          <div className="flex flex-col items-center justify-center p-12 bg-[#F4EFE5] border border-[#D5CEBF] rounded-lg text-center">
            <div className="w-12 h-12 rounded-full bg-[#EBE5D9] border border-[#D5CEBF] flex items-center justify-center mb-3">
              <span className="material-symbols-outlined text-[24px] text-[#4A5550]">
                history_toggle_off
              </span>
            </div>
            <h3 className="font-headline-lg text-[18px] font-bold text-[#121C18] mb-1">
              No audit activity
            </h3>
            <p className="font-body-md text-[13px] text-[#4A5550] max-w-sm mb-4">
              No actions or immutable verification entries have been recorded for the selected filter
              criteria.
            </p>
            <button
              type="button"
              className="px-3.5 py-1.5 rounded-lg bg-[#EBE5D9] border border-[#D5CEBF] text-[#121C18] text-[12px] font-label-sm font-semibold hover:bg-[#E5DEC9] transition-colors cursor-pointer"
              onClick={() => {
                setSelectedActor('all');
                setUserFilter('All Users');
                setActionFilter('All Actions');
                setSearchQuery('');
                setViewState('live');
              }}
            >
              Reset Filters
            </button>
          </div>
        )}

        {/* VIEW CONTAINER 3: SKELETON STATE */}
        {viewState === 'skeleton' && (
          <div className="flex flex-col w-full">
            <div className="w-full bg-[#F4EFE5] border border-[#D5CEBF] rounded-lg overflow-hidden">
              {/* Skeleton Header */}
              <div className="h-9 bg-[#E5DEC9] border-b border-[#D5CEBF] px-3 flex items-center gap-6">
                <div className="w-20 h-3 bg-[#D5CEBF] rounded"></div>
                <div className="w-28 h-3 bg-[#D5CEBF] rounded"></div>
                <div className="w-44 h-3 bg-[#D5CEBF] rounded"></div>
                <div className="w-36 h-3 bg-[#D5CEBF] rounded"></div>
                <div className="w-24 h-3 bg-[#D5CEBF] rounded"></div>
              </div>
              {/* 6 Flat Cream Skeleton Rows (NO pulse/glow) */}
              <div className="divide-y divide-[#DFD9CC]">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="h-11 px-3 flex items-center gap-6 bg-[#F4EFE5]">
                    <div className="w-16 h-3 bg-[#EBE5D9] rounded"></div>
                    <div className="w-32 h-3.5 bg-[#EBE5D9] rounded"></div>
                    <div className="w-48 h-3.5 bg-[#EBE5D9] rounded"></div>
                    <div className="w-40 h-3 bg-[#EBE5D9] rounded"></div>
                    <div className="w-20 h-5 bg-[#EBE5D9] rounded"></div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </ManagerShell>
  );
}
