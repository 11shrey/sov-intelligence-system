'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import ManagerShell from '@/components/layout/ManagerShell';

interface TeamMember {
  id: string;
  name: string;
  initials: string;
  avatarBg: string;
  avatarText: string;
  email: string;
  workerId: string;
  role: string;
  assignedPortfolios: string[];
  activeSessions: number;
  capacityPct: number;
  status: 'optimal' | 'busy' | 'available';
  qualityScore: number;
  governanceLevel: string;
  lastActive: string;
}

const TEAM_MEMBERS: TeamMember[] = [
  {
    id: 'tm-1',
    name: 'Aarav Sharma',
    initials: 'AS',
    avatarBg: 'bg-[#0E3B28]',
    avatarText: 'text-[#F4EFE5]',
    email: 'a.sharma@fidelityrisk.com',
    workerId: 'AS-90412',
    role: 'Risk Ops Worker',
    assignedPortfolios: ['CRE East', 'Industrial Hubs'],
    activeSessions: 3,
    capacityPct: 60,
    status: 'optimal',
    qualityScore: 98.4,
    governanceLevel: 'L2 Schema & Transform',
    lastActive: '5m ago',
  },
  {
    id: 'tm-2',
    name: 'Riya Mehta',
    initials: 'RM',
    avatarBg: 'bg-[#E5DEC9]',
    avatarText: 'text-[#0E3B28]',
    email: 'r.mehta@fidelityrisk.com',
    workerId: 'RM-20941',
    role: 'Risk Analyst',
    assignedPortfolios: ['Commercial Real Estate', 'Midwest Portfolios'],
    activeSessions: 2,
    capacityPct: 40,
    status: 'available',
    qualityScore: 97.9,
    governanceLevel: 'L2 Schema & Transform',
    lastActive: '12m ago',
  },
  {
    id: 'tm-3',
    name: 'Kabir Singh',
    initials: 'KS',
    avatarBg: 'bg-[#E5DEC9]',
    avatarText: 'text-[#0E3B28]',
    email: 'k.singh@fidelityrisk.com',
    workerId: 'KS-88124',
    role: 'Senior Data Cleanser',
    assignedPortfolios: ['Enterprise Property Schedules', 'Catastrophe Exposure'],
    activeSessions: 4,
    capacityPct: 80,
    status: 'busy',
    qualityScore: 99.1,
    governanceLevel: 'L3 Pre-authorization',
    lastActive: '1m ago',
  },
  {
    id: 'tm-4',
    name: 'Alex Rivera',
    initials: 'AR',
    avatarBg: 'bg-[#E5DEC9]',
    avatarText: 'text-[#0E3B28]',
    email: 'a.rivera@fidelityrisk.com',
    workerId: 'AR-31089',
    role: 'Operations Specialist',
    assignedPortfolios: ['Hospitality & Retail', 'Logistics Assets'],
    activeSessions: 2,
    capacityPct: 40,
    status: 'available',
    qualityScore: 96.8,
    governanceLevel: 'L2 Schema & Transform',
    lastActive: '38m ago',
  },
  {
    id: 'tm-5',
    name: 'Ananya Rao',
    initials: 'AR',
    avatarBg: 'bg-[#E5DEC9]',
    avatarText: 'text-[#0E3B28]',
    email: 'a.rao@fidelityrisk.com',
    workerId: 'AR-77402',
    role: 'Risk Ingestion Analyst',
    assignedPortfolios: ['Tri-State Industrial', 'Healthcare Facilities'],
    activeSessions: 1,
    capacityPct: 20,
    status: 'available',
    qualityScore: 98.0,
    governanceLevel: 'L1 Ingestion & Parse',
    lastActive: '1h ago',
  },
];

export default function ManagerTeamPage() {
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [governanceModalOpen, setGovernanceModalOpen] = useState(false);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  };

  const handleRebalance = () => {
    showToast('Workload rebalancing heuristics calculated: 1 session queued from Kabir Singh to Ananya Rao.');
  };

  return (
    <ManagerShell>
      <div className="flex flex-col w-full p-6 space-y-5 text-[#121C18]">
        {/* Header & Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#D5CEBF] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-headline-lg text-[24px] leading-8 font-bold text-[#121C18] tracking-tight">
                Team & Workload
              </h1>
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-label-sm uppercase tracking-wider bg-[#D1F2DE] text-[#0E3B28] font-bold border border-[#00C878]/30">
                <span className="w-1.5 h-1.5 rounded-full bg-[#00C878]"></span>
                5 Workers Active
              </span>
            </div>
            <p className="font-body-md text-[13px] text-[#4A5550] mt-0.5">
              Underwriting operations team allocation, active session capacity, and dual-authorization permissions.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <button
              type="button"
              onClick={handleRebalance}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-label-sm font-semibold rounded bg-[#00C878] text-[#0E3B28] border border-[#00C878] hover:bg-[#7FE3B0] transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">balance</span>
              Auto-Rebalance
            </button>
            <button
              type="button"
              onClick={() => {
                setSelectedMember(TEAM_MEMBERS[0]);
                setGovernanceModalOpen(true);
              }}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-label-sm font-semibold rounded bg-[#F4EFE5] border border-[#D5CEBF] text-[#121C18] hover:bg-[#EBE5D9] transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">policy</span>
              Governance Roles
            </button>
          </div>
        </div>

        {/* Feedback Toast */}
        {toastMessage && (
          <div className="p-3 bg-[#D1F2DE] border border-[#00C878] rounded text-xs text-[#0E3B28] flex items-center justify-between font-label-sm font-semibold">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">verified</span>
              <span>{toastMessage}</span>
            </div>
            <button
              type="button"
              onClick={() => setToastMessage(null)}
              className="text-[#0E3B28] font-bold text-xs"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Top KPI Metrics Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1 */}
          <div className="bg-[#F4EFE5] border border-[#D5CEBF] rounded p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-label-sm text-xs font-semibold uppercase tracking-wider text-[#4A5550]">
                Active Operators
              </span>
              <span className="w-2 h-2 rounded-full bg-[#00C878]"></span>
            </div>
            <div className="my-2">
              <span className="font-headline-lg text-3xl font-bold text-[#0E3B28] tracking-tight">5 / 5</span>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] font-body-md text-[#4A5550]">
              <span className="font-label-sm font-semibold text-[#0E3B28]">100% on duty</span>
              <span>· Zero absenteeism</span>
            </div>
          </div>

          {/* Card 2 */}
          <div className="bg-[#F4EFE5] border border-[#D5CEBF] rounded p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-label-sm text-xs font-semibold uppercase tracking-wider text-[#4A5550]">
                Team Utilization
              </span>
              <span className="w-2 h-2 rounded-full bg-[#00C878]"></span>
            </div>
            <div className="my-2">
              <span className="font-headline-lg text-3xl font-bold text-[#00C878] tracking-tight">48%</span>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] font-body-md text-[#4A5550]">
              <span className="font-label-sm font-semibold text-[#0E3B28]">Optimal band</span>
              <span>(Target 40-75%)</span>
            </div>
          </div>

          {/* Card 3 */}
          <div className="bg-[#F4EFE5] border border-[#D5CEBF] rounded p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-label-sm text-xs font-semibold uppercase tracking-wider text-[#4A5550]">
                Sessions In Flight
              </span>
              <span className="w-2 h-2 rounded-full bg-[#B87A1E]"></span>
            </div>
            <div className="my-2">
              <span className="font-headline-lg text-3xl font-bold text-[#B87A1E] tracking-tight">12</span>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] font-body-md text-[#4A5550]">
              <span className="font-semibold text-[#B87A1E]">5 awaiting review</span>
              <span>· 7 in pipeline</span>
            </div>
          </div>

          {/* Card 4 */}
          <div className="bg-[#F4EFE5] border border-[#D5CEBF] rounded p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-label-sm text-xs font-semibold uppercase tracking-wider text-[#4A5550]">
                Mean Quality Score
              </span>
              <span className="material-symbols-outlined text-xs text-[#8B9490]">star</span>
            </div>
            <div className="my-2">
              <span className="font-headline-lg text-3xl font-bold text-[#121C18] tracking-tight">98.1%</span>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] font-body-md text-[#4A5550]">
              <span className="px-1.5 py-0.5 rounded text-[10px] font-label-sm font-semibold bg-[#D1F2DE] text-[#0E3B28]">
                L4 Pass Rate: 99.4%
              </span>
            </div>
          </div>
        </div>

        {/* Main 2-Column Split: Team Roster Table (8 cols) & Workload Allocation Card (4 cols) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* LEFT: Team Roster Table */}
          <div className="lg:col-span-8 bg-[#F4EFE5] border border-[#D5CEBF] rounded flex flex-col justify-between">
            <div className="p-4 border-b border-[#D5CEBF] bg-[#EBE5D9] flex items-center justify-between">
              <div>
                <h2 className="font-headline-lg text-sm font-semibold text-[#121C18]">Team Roster</h2>
                <p className="font-body-md text-xs text-[#4A5550]">
                  Active underwriting operators and dual-authorization credentials
                </p>
              </div>
              <span className="font-label-sm text-xs text-[#0E3B28] font-bold">5 Members</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse min-w-[640px]">
                <thead>
                  <tr className="bg-[#E5DEC9] border-b border-[#D5CEBF] font-label-sm uppercase tracking-wider text-[11px] text-[#4A5550] h-9">
                    <th className="py-2 px-3 font-medium">Worker</th>
                    <th className="py-2 px-3 font-medium">Portfolios</th>
                    <th className="py-2 px-3 font-medium">Capacity</th>
                    <th className="py-2 px-3 font-medium">Quality</th>
                    <th className="py-2 px-3 font-medium">Role Gate</th>
                    <th className="py-2 px-3 text-right font-medium">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#DFD9CC] font-body-md text-[12px] text-[#121C18]">
                  {TEAM_MEMBERS.map((member) => (
                    <tr key={member.id} className="hover:bg-[#EBE5D9]/40 transition-colors h-14">
                      {/* Worker info */}
                      <td className="py-2 px-3 align-middle">
                        <div className="flex items-center gap-2.5">
                          <div
                            className={`w-7 h-7 rounded-full ${member.avatarBg} ${member.avatarText} text-[10px] font-semibold flex items-center justify-center`}
                          >
                            {member.initials}
                          </div>
                          <div>
                            <div className="font-headline-lg font-bold text-xs text-[#121C18]">
                              {member.name}
                            </div>
                            <div className="text-[10px] text-[#8B9490] font-mono-code">
                              {member.workerId} · {member.email}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Portfolios */}
                      <td className="py-2 px-3 align-middle text-[11px]">
                        <div className="text-[#121C18] font-medium truncate max-w-[150px]">
                          {member.assignedPortfolios[0]}
                        </div>
                        <div className="text-[#8B9490] text-[10px]">
                          +{member.assignedPortfolios.length - 1} secondary
                        </div>
                      </td>

                      {/* Capacity Bar */}
                      <td className="py-2 px-3 align-middle">
                        <div className="space-y-1 w-28">
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="font-semibold text-[#121C18]">
                              {member.activeSessions} active
                            </span>
                            <span
                              className={`font-label-sm text-[10px] font-bold ${
                                member.capacityPct >= 80
                                  ? 'text-[#B87A1E]'
                                  : member.capacityPct >= 50
                                  ? 'text-[#0E3B28]'
                                  : 'text-[#4A5550]'
                              }`}
                            >
                              {member.capacityPct}%
                            </span>
                          </div>
                          <div className="w-full h-1.5 bg-[#D5CEBF] rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                member.capacityPct >= 80 ? 'bg-[#B87A1E]' : 'bg-[#00C878]'
                              }`}
                              style={{ width: `${member.capacityPct}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>

                      {/* Quality */}
                      <td className="py-2 px-3 align-middle font-mono text-[11px]">
                        <span className="font-semibold text-[#0E3B28]">{member.qualityScore}%</span>
                        <span className="text-[10px] text-[#8B9490] block">0 audit flags</span>
                      </td>

                      {/* Role Gate */}
                      <td className="py-2 px-3 align-middle">
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-label-sm font-semibold bg-[#E5DEC9] text-[#0E3B28] border border-[#D5CEBF]">
                          {member.governanceLevel}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="py-2 px-3 align-middle text-right">
                        <Link
                          href="/manager/queue"
                          className="px-2.5 py-1 text-[11px] font-label-sm font-bold rounded bg-[#F4EFE5] border border-[#D5CEBF] text-[#121C18] hover:bg-[#EBE5D9] transition-colors"
                        >
                          Queue →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-3 border-t border-[#D5CEBF] bg-[#EBE5D9] flex items-center justify-between text-[11px] text-[#4A5550]">
              <span>All 5 workers authenticated via SSO HSM Credentials</span>
              <span className="font-label-sm font-semibold text-[#0E3B28]">Directory Synced</span>
            </div>
          </div>

          {/* RIGHT: Workload Distribution & Real-time Allocation */}
          <div className="lg:col-span-4 bg-[#F4EFE5] border border-[#D5CEBF] rounded flex flex-col justify-between">
            <div className="p-4 border-b border-[#D5CEBF] bg-[#EBE5D9] flex items-center justify-between">
              <div>
                <h2 className="font-headline-lg text-sm font-semibold text-[#121C18]">
                  Capacity Allocation
                </h2>
                <p className="font-body-md text-xs text-[#4A5550]">Load balancing distribution</p>
              </div>
              <span className="w-2 h-2 rounded-full bg-[#00C878]"></span>
            </div>

            <div className="p-4 space-y-4">
              {TEAM_MEMBERS.map((worker) => (
                <div key={worker.id} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-5 h-5 rounded-full ${worker.avatarBg} ${worker.avatarText} text-[10px] font-semibold flex items-center justify-center`}
                      >
                        {worker.initials}
                      </span>
                      <span className="font-headline-lg font-medium text-[#121C18]">
                        {worker.name}
                      </span>
                    </div>
                    <span
                      className={`font-label-sm text-[11px] ${
                        worker.capacityPct >= 80 ? 'text-[#B87A1E] font-bold' : 'text-[#4A5550]'
                      }`}
                    >
                      {worker.activeSessions} active ({worker.capacityPct}%)
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-[#D5CEBF] rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        worker.capacityPct >= 80 ? 'bg-[#B87A1E]' : 'bg-[#00C878]'
                      }`}
                      style={{ width: `${worker.capacityPct}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>

            <div className="p-3 border-t border-[#D5CEBF] bg-[#EBE5D9] flex flex-col gap-2 text-[11px]">
              <div className="flex items-center justify-between">
                <span className="font-body-md text-[#4A5550]">Aggregate Load</span>
                <span className="font-headline-lg font-bold text-[#0E3B28]">48% Optimal</span>
              </div>
              <p className="text-[10px] text-[#8B9490]">
                Threshold for dual-authorization auto-escalation is 85% individual utilization.
              </p>
            </div>
          </div>
        </div>

        {/* Governance Level Drawer / Modal */}
        {governanceModalOpen && selectedMember && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
            <div className="w-full max-w-lg bg-[#F4EFE5] border border-[#D5CEBF] rounded-lg shadow-xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#D5CEBF] pb-3">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[20px] text-[#0E3B28]">
                    verified_user
                  </span>
                  <h3 className="font-headline-lg text-base font-bold text-[#121C18]">
                    Governance Authorization Gate
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={() => setGovernanceModalOpen(false)}
                  className="text-[#4A5550] hover:text-[#121C18]"
                >
                  <span className="material-symbols-outlined text-[18px]">close</span>
                </button>
              </div>

              <div className="space-y-3 text-xs">
                <div className="p-3 bg-[#EBE5D9] border border-[#D5CEBF] rounded">
                  <div className="font-semibold text-sm text-[#121C18]">{selectedMember.name}</div>
                  <div className="text-[11px] text-[#8B9490] font-mono-code">
                    {selectedMember.workerId} · Role: {selectedMember.role}
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="font-label-sm uppercase tracking-wider text-[11px] font-bold text-[#4A5550]">
                    Authorized Permission Tier
                  </label>
                  <div className="space-y-1.5">
                    <label className="flex items-center gap-2 p-2 bg-[#F4EFE5] border border-[#D5CEBF] rounded cursor-pointer">
                      <input type="radio" name="govLevel" defaultChecked className="accent-[#00C878]" />
                      <div>
                        <div className="font-semibold text-[#121C18]">L2: Schema Mapping & DQ Fixes</div>
                        <div className="text-[10px] text-[#4A5550]">
                          Worker can ingest workbooks, edit field mappings, and propose transformation rules.
                        </div>
                      </div>
                    </label>
                    <label className="flex items-center gap-2 p-2 bg-[#F4EFE5] border border-[#D5CEBF] rounded cursor-pointer">
                      <input type="radio" name="govLevel" className="accent-[#00C878]" />
                      <div>
                        <div className="font-semibold text-[#121C18]">L3: Senior Pre-Authorization</div>
                        <div className="text-[10px] text-[#4A5550]">
                          Can perform batch overrides and approve minor variances up to 5% cost basis.
                        </div>
                      </div>
                    </label>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#D5CEBF]">
                <button
                  type="button"
                  onClick={() => setGovernanceModalOpen(false)}
                  className="px-3 py-1.5 rounded text-xs text-[#4A5550] hover:bg-[#EBE5D9]"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setGovernanceModalOpen(false);
                    showToast(`Updated governance authorization tier for ${selectedMember.name}.`);
                  }}
                  className="px-3.5 py-1.5 rounded text-xs font-semibold bg-[#00C878] text-[#0E3B28] hover:bg-[#7FE3B0]"
                >
                  Save Governance Scope
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </ManagerShell>
  );
}
