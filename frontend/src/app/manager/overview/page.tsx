'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import ManagerShell from '@/components/layout/ManagerShell';
import { useWorkflowStore } from '@/store/workflow-store';

export default function ManagerTeamOverviewPage() {
  const router = useRouter();
  const { sessions, setActiveSessionId } = useWorkflowStore();
  const [dashboardState, setDashboardState] = useState<'active' | 'empty' | 'skeleton'>('active');
  const [timeRange, setTimeRange] = useState<'today' | '7d' | '30d'>('7d');

  const awaitingSessions = sessions.filter((s) => s.status === 'awaiting' || s.status === 'ready');
  const approvedSessionsCount = sessions.filter((s) => s.status === 'approved').length;
  const returnedSessionsCount = sessions.filter((s) => s.status === 'returned').length;

  // Derive dynamic metrics based on time range + session states
  const approvedDisplayCount = timeRange === 'today' ? 4 + approvedSessionsCount : timeRange === '30d' ? 62 + approvedSessionsCount : 18 + approvedSessionsCount;
  const returnedDisplayCount = timeRange === 'today' ? 1 + returnedSessionsCount : timeRange === '30d' ? 9 + returnedSessionsCount : 3 + returnedSessionsCount;

  const handleReview = (id: string) => {
    setActiveSessionId(id);
    router.push(`/manager/review?id=${id}`);
  };

  return (
    <ManagerShell>
      <div className="flex flex-col w-full space-y-5">
        {/* Header & Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
          <div>
            <h1 className="font-heading text-2xl sm:text-3xl font-bold text-[#121C18] tracking-tight">
              Team Overview
            </h1>
            <p className="font-sans text-xs sm:text-sm text-[#4A5550] mt-0.5">
              Underwriting operations and transformation queue status across CRE portfolios.
            </p>
          </div>
          <div className="flex items-center gap-2 self-start sm:self-auto">
            {/* Date Range Selector */}
            <div className="relative inline-flex items-center">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as 'today' | '7d' | '30d')}
                className="appearance-none bg-[#F4EFE5] border border-[#D5CEBF] rounded px-3 py-1.5 pr-8 font-heading text-xs font-medium text-[#121C18] hover:bg-[#EBE5D9] transition-colors focus:outline-none cursor-pointer"
              >
                <option value="7d">Last 7 days</option>
                <option value="today">Today</option>
                <option value="30d">Last 30 days</option>
              </select>
              <span className="material-symbols-outlined text-[#8B9490] absolute right-2 pointer-events-none text-base">
                expand_more
              </span>
            </div>

            {/* Demo View Switcher */}
            <div className="inline-flex items-center bg-[#EBE5D9] border border-[#D5CEBF] rounded p-0.5">
              <button
                type="button"
                onClick={() => setDashboardState('active')}
                className={`px-2.5 py-1 text-xs font-tag font-semibold rounded transition-colors cursor-pointer ${
                  dashboardState === 'active'
                    ? 'bg-[#00C878] text-[#0E3B28]'
                    : 'text-[#4A5550] hover:text-[#121C18]'
                }`}
              >
                Active
              </button>
              <button
                type="button"
                onClick={() => setDashboardState('empty')}
                className={`px-2.5 py-1 text-xs font-tag font-medium rounded transition-colors cursor-pointer ${
                  dashboardState === 'empty'
                    ? 'bg-[#00C878] text-[#0E3B28] font-semibold'
                    : 'text-[#4A5550] hover:text-[#121C18]'
                }`}
              >
                Clear
              </button>
              <button
                type="button"
                onClick={() => setDashboardState('skeleton')}
                className={`px-2.5 py-1 text-xs font-tag font-medium rounded transition-colors cursor-pointer ${
                  dashboardState === 'skeleton'
                    ? 'bg-[#00C878] text-[#0E3B28] font-semibold'
                    : 'text-[#4A5550] hover:text-[#121C18]'
                }`}
              >
                Skeleton
              </button>
            </div>
          </div>
        </div>

        {/* Skeleton View */}
        {dashboardState === 'skeleton' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-28 bg-[#EBE5D9] border border-[#D5CEBF] rounded p-4 space-y-3">
                <div className="w-24 h-3 bg-[#D5CEBF] rounded"></div>
                <div className="w-12 h-6 bg-[#D5CEBF] rounded"></div>
                <div className="w-32 h-2.5 bg-[#D5CEBF] rounded"></div>
              </div>
            ))}
          </div>
        )}

        {/* Empty View */}
        {dashboardState === 'empty' && (
          <div className="flex flex-col items-center justify-center p-12 bg-[#F4EFE5] border border-[#D5CEBF] rounded-xl text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-[#D1F2DE] border border-[#00C878] flex items-center justify-center text-[#0E3B28]">
              <span className="material-symbols-outlined text-2xl">verified</span>
            </div>
            <div className="space-y-1">
              <h2 className="font-heading text-lg font-semibold text-[#121C18]">Queue is clear</h2>
              <p className="font-sans text-sm text-[#4A5550] max-w-md">
                No portfolio submissions currently require manager dual-authorization. All team workstreams are running within standard SLA bounds.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setDashboardState('active')}
              className="px-4 py-1.5 text-xs font-tag font-semibold rounded bg-[#00C878] text-[#0E3B28] hover:bg-[#00b56c] transition-colors cursor-pointer shadow-none"
            >
              Simulate Active Submissions
            </button>
          </div>
        )}

        {/* Active View */}
        {dashboardState === 'active' && (
          <div className="flex flex-col w-full space-y-5">
            {/* Row 1: KPI Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-[#F4EFE5] border border-[#D5CEBF] rounded-lg p-4 flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="font-tag text-xs font-semibold uppercase tracking-wider text-[#4A5550]">
                    Awaiting My Review
                  </span>
                  <span className="w-2 h-2 rounded-full bg-[#B87A1E]"></span>
                </div>
                <div className="my-2">
                  <span className="font-heading text-3xl font-bold text-[#B87A1E] tracking-tight">
                    {awaitingSessions.length}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-tag font-bold bg-[#F7ECC8] text-[#B87A1E] border border-[#D5CEBF]">
                    Requires attention
                  </span>
                  <span className="font-sans text-[11px] text-[#4A5550]">within SLA</span>
                </div>
              </div>

              <div className="bg-[#F4EFE5] border border-[#D5CEBF] rounded-lg p-4 flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="font-tag text-xs font-semibold uppercase tracking-wider text-[#4A5550]">
                    Approved {timeRange === 'today' ? 'Today' : timeRange === '30d' ? 'Last 30d' : 'This Week'}
                  </span>
                  <span className="w-2 h-2 rounded-full bg-[#00C878]"></span>
                </div>
                <div className="my-2">
                  <span className="font-heading text-3xl font-bold text-[#00C878] tracking-tight">
                    {approvedDisplayCount}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="font-tag text-xs font-semibold text-[#0E3B28]">+{approvedSessionsCount > 0 ? approvedSessionsCount : 4}</span>
                  <span className="font-sans text-[11px] text-[#4A5550]">velocity benchmark</span>
                </div>
              </div>

              <div className="bg-[#F4EFE5] border border-[#D5CEBF] rounded-lg p-4 flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="font-tag text-xs font-semibold uppercase tracking-wider text-[#4A5550]">
                    Returned for Rework
                  </span>
                  <span className="w-2 h-2 rounded-full bg-[#8C3B24]"></span>
                </div>
                <div className="my-2">
                  <span className="font-heading text-3xl font-bold text-[#8C3B24] tracking-tight">
                    {returnedDisplayCount}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="font-sans text-[11px] text-[#8C3B24]">
                    Pending worker remediation
                  </span>
                </div>
              </div>

              <div className="bg-[#F4EFE5] border border-[#D5CEBF] rounded-lg p-4 flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="font-tag text-xs font-semibold uppercase tracking-wider text-[#4A5550]">
                    Avg Review Turnaround
                  </span>
                  <span className="material-symbols-outlined text-xs text-[#8B9490]">timer</span>
                </div>
                <div className="my-2">
                  <span className="font-heading text-3xl font-bold text-[#121C18] tracking-tight">
                    2h 14m
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-tag font-semibold bg-[#D1F2DE] text-[#0E3B28]">
                    Target: &lt; 4h (100% SLA)
                  </span>
                </div>
              </div>
            </div>

            {/* Row 2: Split 2/3 (Needs Review) & 1/3 (Team Workload) */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
              {/* Left Column: Needs Review */}
              <div className="lg:col-span-8 bg-[#F4EFE5] border border-[#D5CEBF] rounded-xl flex flex-col justify-between overflow-hidden">
                <div className="p-4 border-b border-[#D5CEBF] bg-[#EBE5D9] flex items-center justify-between">
                  <div>
                    <h2 className="font-heading text-sm font-bold text-[#121C18]">Needs Review</h2>
                    <p className="font-sans text-xs text-[#4A5550]">
                      Submissions awaiting manager dual-authorization
                    </p>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[11px] font-tag font-bold bg-[#F7ECC8] text-[#B87A1E] border border-[#D5CEBF]">
                    {awaitingSessions.length} Pending Sign-Off
                  </span>
                </div>

                <div className="divide-y divide-[#D5CEBF] overflow-x-auto">
                  {awaitingSessions.length === 0 ? (
                    <div className="py-10 px-4 text-center">
                      <span className="material-symbols-outlined text-[#8B9490] text-3xl mb-1">
                        task_alt
                      </span>
                      <p className="font-heading text-xs font-bold text-[#121C18]">
                        All submissions processed
                      </p>
                      <p className="font-sans text-[11px] text-[#4A5550] mt-0.5">
                        No submissions currently require Level 4 manager dual-authorization.
                      </p>
                    </div>
                  ) : (
                    awaitingSessions.map((s) => (
                      <div
                        key={s.id}
                        className="px-4 py-3 flex items-center justify-between hover:bg-[#EBE5D9] transition-colors gap-3"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <span className="material-symbols-outlined text-[#8B9490] text-lg shrink-0">
                            description
                          </span>
                          <div className="min-w-0">
                            <div className="font-heading text-xs font-bold text-[#121C18] truncate">
                              {s.fileName}
                            </div>
                            <div className="flex items-center gap-2 font-sans text-[11px] text-[#4A5550]">
                              <span className="inline-flex items-center gap-1">
                                <span className="w-4 h-4 rounded-full bg-[#E5DEC9] border border-[#D5CEBF] text-[9px] font-semibold text-[#0E3B28] flex items-center justify-center">
                                  {s.workerAvatar}
                                </span>
                                {s.workerName}
                              </span>
                              <span>•</span>
                              <span>{s.rowCount} records</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-4 shrink-0">
                          <div className="text-right">
                            <span className="font-tag text-xs font-semibold text-[#B87A1E]">
                              2h 14m waiting
                            </span>
                            <div className="font-tag text-[10px] text-[#8B9490]">L4 Gate pending</div>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleReview(s.id)}
                            className="px-3.5 py-1.5 text-xs font-tag font-bold rounded-full bg-[#00C878] text-[#0E3B28] hover:bg-[#00b56c] transition-colors flex items-center gap-1 cursor-pointer shadow-none"
                          >
                            Review <span>→</span>
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>

                <div className="p-3 border-t border-[#D5CEBF] bg-[#EBE5D9] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                  <span className="font-sans text-[11px] text-[#8B9490]">
                    Review actions route directly to maker-checker cryptographic sign-off
                  </span>
                  <Link
                    href="/manager/queue"
                    className="font-tag text-xs font-bold text-[#0E3B28] hover:underline flex items-center gap-1"
                  >
                    View all in Approval Queue <span>→</span>
                  </Link>
                </div>
              </div>

              {/* Right Column: Team Workload */}
              <div className="lg:col-span-4 bg-[#F4EFE5] border border-[#D5CEBF] rounded-xl flex flex-col justify-between overflow-hidden">
                <div className="p-4 border-b border-[#D5CEBF] bg-[#EBE5D9] flex items-center justify-between">
                  <div>
                    <h2 className="font-heading text-sm font-bold text-[#121C18]">Team Workload</h2>
                    <p className="font-sans text-xs text-[#4A5550]">Active transformation capacity</p>
                  </div>
                  <span className="font-tag text-xs text-[#0E3B28] font-bold">5 Workers</span>
                </div>

                <div className="p-4 space-y-4">
                  {[
                    { name: 'Aarav Sharma', avatar: 'AS', sessions: '3 active sessions (60%)', pct: 60 },
                    { name: 'Riya Mehta', avatar: 'RM', sessions: '2 active sessions (40%)', pct: 40 },
                    { name: 'Kabir Singh', avatar: 'KS', sessions: '4 active sessions (80%)', pct: 80 },
                    { name: 'Alex Rivera', avatar: 'AR', sessions: '2 active sessions (40%)', pct: 40 },
                    { name: 'Ananya Rao', avatar: 'AR', sessions: '1 active session (20%)', pct: 20 },
                  ].map((worker, idx) => (
                    <div key={idx} className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-[#0E3B28] text-[#F4EFE5] text-[10px] font-semibold flex items-center justify-center">
                            {worker.avatar}
                          </span>
                          <span className="font-heading font-medium text-[#121C18]">{worker.name}</span>
                        </div>
                        <span className="font-tag text-[#4A5550]">{worker.sessions}</span>
                      </div>
                      <div className="w-full h-1.5 bg-[#D5CEBF] rounded-full overflow-hidden">
                        <div
                          className="h-full bg-[#00C878] rounded-full"
                          style={{ width: `${worker.pct}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="p-3 border-t border-[#D5CEBF] bg-[#EBE5D9] flex items-center justify-between text-[11px]">
                  <span className="font-sans text-[#4A5550]">Team Utilization</span>
                  <span className="font-heading font-bold text-[#0E3B28]">48% Optimal</span>
                </div>
              </div>
            </div>

            {/* Row 3: Recent Activity (Immutable Audit Log) */}
            <div className="bg-[#F4EFE5] border border-[#D5CEBF] rounded-xl overflow-hidden">
              <div className="p-4 border-b border-[#D5CEBF] bg-[#EBE5D9] flex items-center justify-between">
                <div>
                  <h2 className="font-heading text-sm font-bold text-[#121C18]">Recent Activity</h2>
                  <p className="font-sans text-xs text-[#4A5550]">
                    Immutable audit log of team submissions and governance decisions
                  </p>
                </div>
                <div className="flex items-center gap-1.5 text-xs font-tag text-[#0E3B28]">
                  <span className="w-2 h-2 rounded-full bg-[#00C878]"></span>
                  <span>Ledger Synced</span>
                </div>
              </div>

              <div className="divide-y divide-[#D5CEBF]">
                {[
                  {
                    time: '10:42 AM',
                    actor: 'Aarav Sharma',
                    action: 'Submitted Property_SOV_Jan.xlsx for review',
                    status: 'Awaiting Review',
                    color: '#B87A1E',
                    bg: '#F7ECC8',
                  },
                  {
                    time: '10:18 AM',
                    actor: 'S. Reynolds (Manager)',
                    action: 'Approved WestSite_SOV.xlsx',
                    status: 'Approved',
                    color: '#0E3B28',
                    bg: '#D1F2DE',
                  },
                  {
                    time: '09:56 AM',
                    actor: 'S. Reynolds (Manager)',
                    action: 'Returned MetroAssets_SOV.xlsx (Replacement Cost variance)',
                    status: 'Returned',
                    color: '#8C3B24',
                    bg: '#FBEBE8',
                  },
                  {
                    time: '09:18 AM',
                    actor: 'Riya Mehta',
                    action: 'Submitted NorthPlant_SOV.xlsx for review',
                    status: 'Awaiting Review',
                    color: '#B87A1E',
                    bg: '#F7ECC8',
                  },
                ].map((act, idx) => (
                  <div
                    key={idx}
                    className="px-4 py-2.5 flex items-center justify-between hover:bg-[#EBE5D9] transition-colors text-xs"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="w-2 h-2 rounded-full bg-[#00C878] shrink-0"></span>
                      <span className="font-tag text-[#8B9490] w-16 shrink-0">{act.time}</span>
                      <span className="font-heading font-semibold text-[#121C18] truncate">
                        {act.actor}
                      </span>
                      <span className="font-sans text-[#4A5550] truncate">{act.action}</span>
                    </div>
                    <span
                      className="px-2 py-0.5 rounded text-[11px] font-tag font-semibold border border-[#D5CEBF] shrink-0"
                      style={{ backgroundColor: act.bg, color: act.color }}
                    >
                      {act.status}
                    </span>
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
