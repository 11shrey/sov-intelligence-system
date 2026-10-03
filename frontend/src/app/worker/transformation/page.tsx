'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import WorkerShell from '@/components/layout/WorkerShell';

export default function WorkerTransformationPage() {
  const router = useRouter();
  const [progress, setProgress] = useState(86);
  const [rows, setRows] = useState(724);
  const totalRows = 842;

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev < 100) {
          const next = prev + 2;
          setRows(Math.min(totalRows, Math.floor((next / 100) * totalRows)));
          return next;
        }
        clearInterval(interval);
        setRows(totalRows);
        return 100;
      });
    }, 400);
    return () => clearInterval(interval);
  }, []);

  return (
    <WorkerShell>
      <div className="flex flex-col w-full max-w-7xl mx-auto space-y-6 pb-12">
        {/* Top Navigation & Governance Context */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-1.5 font-tag text-xs text-[#8B9490] tracking-wide">
              <Link href="/worker/dashboard" className="hover:text-[#121C18]">
                SOVIA Hub
              </Link>
              <span className="font-bold">›</span>
              <span>Pipeline Ingestion</span>
              <span className="font-bold">›</span>
              <span className="text-[#4A5550] font-semibold">Deterministic Transformation Engine</span>
            </div>
            <div className="flex items-baseline gap-3 flex-wrap">
              <h1 className="font-heading text-2xl sm:text-3xl font-bold tracking-tight text-[#121C18]">
                Applying Transformations
              </h1>
              <span className="font-tag text-xs font-bold tracking-wider text-[#0E3B28] uppercase bg-[#D1F2DE] px-2.5 py-0.5 rounded-full border border-[#7FE3B0]">
                Partition Alpha-04
              </span>
            </div>
            <p className="font-sans text-sm text-[#4A5550] max-w-3xl mt-0.5">
              Applying human-approved mappings, schema standardizations, and actuarial cleansing rules with strict tamper-evident logging.
            </p>
          </div>
          <div className="self-start md:self-center flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => {
                setProgress(20);
                setRows(168);
              }}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border border-[#D5CEBF] bg-[#EBE5D9] hover:bg-[#E5DEC9] text-xs font-heading font-semibold text-[#121C18] transition-colors cursor-pointer"
            >
              <span className={`material-symbols-outlined text-[16px] ${progress < 100 ? 'animate-spin' : ''}`}>
                sync
              </span>
              <span>Re-run Engine</span>
            </button>
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg border border-[#D5CEBF] bg-[#EBE5D9]">
              <span className="material-symbols-outlined text-[18px] text-[#0E3B28]">verified_user</span>
              <span className="font-tag text-xs text-[#121C18] font-bold">
                Governance Gate 03 / Executing
              </span>
            </div>
          </div>
        </div>

        {/* Execution Progress Checklist Card */}
        <div className="rounded-xl p-6 bg-[#EBE5D9] border border-[#D5CEBF] space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between p-3.5 rounded-lg border border-[#D5CEBF] bg-[#F4EFE5]">
            <div className="flex items-center gap-2.5">
              <span className="material-symbols-outlined text-[#0E3B28] text-[20px]">sync</span>
              <span className="font-heading text-sm font-bold text-[#121C18]">
                Execution Sequence: Canonical Normalization Pipeline
              </span>
            </div>
            <div className="flex items-center gap-3 mt-2 md:mt-0 font-tag text-xs text-[#8B9490]">
              <span>
                Session ID: <code className="font-mono font-medium text-[#121C18]">SES-2025-01-9844</code>
              </span>
              <span>•</span>
              <span>
                Worker Pool: <span className="text-[#121C18] font-semibold">Node-Actuary-02</span>
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Step 1 */}
            <div className="flex flex-col rounded-lg p-4 border border-[#D5CEBF] bg-[#F4EFE5]">
              <div className="flex items-center justify-between mb-2">
                <div className="w-7 h-7 rounded-full flex items-center justify-center text-[#0E3B28] font-bold bg-[#00C878]">
                  <span className="material-symbols-outlined text-[16px]">check</span>
                </div>
                <span className="font-tag text-[11px] font-semibold px-2 py-0.5 rounded bg-[#EBE5D9] text-[#4A5550]">
                  0.8s
                </span>
              </div>
              <span className="font-heading text-[13px] font-bold text-[#121C18] mb-1">
                1. Validating mappings
              </span>
              <p className="font-sans text-xs text-[#4A5550] leading-relaxed mb-2">
                15 canonical mappings validated against schema ISO-2025 standard. Zero circular dependencies.
              </p>
              <span className="font-tag text-[11px] text-[#0E3B28] mt-auto font-bold">
                Canonical Schema: Passed
              </span>
            </div>

            {/* Step 2 */}
            <div className="flex flex-col rounded-lg p-4 border border-[#D5CEBF] bg-[#F4EFE5]">
              <div className="flex items-center justify-between mb-2">
                <div className="w-7 h-7 rounded-full flex items-center justify-center text-[#0E3B28] font-bold bg-[#00C878]">
                  <span className="material-symbols-outlined text-[16px]">check</span>
                </div>
                <span className="font-tag text-[11px] font-semibold px-2 py-0.5 rounded bg-[#EBE5D9] text-[#4A5550]">
                  1.4s
                </span>
              </div>
              <span className="font-heading text-[13px] font-bold text-[#121C18] mb-1">
                2. Standardizing formats
              </span>
              <p className="font-sans text-xs text-[#4A5550] leading-relaxed mb-2">
                Normalized monetary strings, parsed date formats, and converted address casing across 842 records.
              </p>
              <span className="font-tag text-[11px] text-[#0E3B28] mt-auto font-bold">
                842 Records Harmonized
              </span>
            </div>

            {/* Step 3 */}
            <div className="flex flex-col rounded-lg p-4 border border-[#D5CEBF] bg-[#F4EFE5]">
              <div className="flex items-center justify-between mb-2">
                <div className="w-7 h-7 rounded-full flex items-center justify-center text-[#0E3B28] font-bold bg-[#00C878]">
                  <span className="material-symbols-outlined text-[16px]">check</span>
                </div>
                <span className="font-tag text-[11px] font-semibold px-2 py-0.5 rounded bg-[#EBE5D9] text-[#4A5550]">
                  1.9s
                </span>
              </div>
              <span className="font-heading text-[13px] font-bold text-[#121C18] mb-1">
                3. Cleaning invalid values
              </span>
              <p className="font-sans text-xs text-[#4A5550] leading-relaxed mb-2">
                Resolved negative replacement costs via absolute inversion; geocoded postal code mismatches.
              </p>
              <span className="font-tag text-[11px] text-[#0E3B28] mt-auto font-bold">
                Deterministic Rules Applied
              </span>
            </div>

            {/* Step 4 */}
            <div className="flex flex-col rounded-lg p-4 border border-[#7FE3B0] bg-[#F4EFE5]">
              <div className="flex items-center justify-between mb-2">
                <div className="w-7 h-7 rounded-full flex items-center justify-center text-[#0E3B28] bg-[#00C878]">
                  {progress < 100 ? (
                    <span className="material-symbols-outlined text-[16px] animate-spin">
                      progress_activity
                    </span>
                  ) : (
                    <span className="material-symbols-outlined text-[16px] font-bold">check</span>
                  )}
                </div>
                <span className="font-tag text-[11px] font-bold px-2 py-0.5 rounded bg-[#D1F2DE] text-[#0E3B28] border border-[#7FE3B0]">
                  {progress < 100 ? 'Running' : 'Complete'}
                </span>
              </div>
              <span className="font-heading text-[13px] font-bold text-[#121C18] mb-1">
                4. Applying transformations
              </span>
              <p className="font-sans text-xs text-[#4A5550] leading-relaxed mb-2">
                Executing deterministic SQL/DataFrame rules across target schema partition.
              </p>
              <span className="font-tag text-[11px] font-bold mt-auto text-[#0E3B28]">
                Completed: {rows} / {totalRows} ({progress}%)
              </span>
            </div>
          </div>

          <div className="p-4 rounded-lg border border-[#D5CEBF] bg-[#F4EFE5]">
            <div className="flex items-center justify-between mb-2 font-tag text-xs">
              <span className="text-[#4A5550] flex items-center gap-1.5 font-medium">
                <span className="w-2 h-2 rounded-full inline-block bg-[#00C878]"></span>
                Data Processing Pipeline Phase 4/4
              </span>
              <span className="text-[#121C18] font-mono text-[12px] font-medium">
                Est. remaining: ~{progress === 100 ? '0' : '1.2'}s · Memory: 54MB · CPU: 12.4%
              </span>
            </div>
            <div className="w-full h-2.5 rounded-full overflow-hidden bg-[#E5DEC9] border border-[#D5CEBF]">
              <div
                className="h-full bg-[#00C878] rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Side-by-Side Audit Panels */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Approved Changes Panel */}
          <div className="rounded-xl p-5 bg-[#EBE5D9] border border-[#D5CEBF] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#D5CEBF]">
                <div className="flex items-center gap-2 flex-wrap">
                  <h2 className="font-heading text-base font-bold text-[#121C18]">Approved Changes</h2>
                  <span className="px-2.5 py-0.5 rounded-full font-tag text-[11px] font-bold bg-[#D1F2DE] text-[#0E3B28] border border-[#7FE3B0]">
                    18 Approved to Apply
                  </span>
                </div>
                <span className="font-tag text-xs text-[#8B9490]">Scope: Target Model</span>
              </div>
              <p className="font-sans text-xs text-[#4A5550] mb-4">
                Changes authorized during human review — deterministic application without stochastic extrapolation.
              </p>

              <div className="flex flex-col gap-2.5">
                {[
                  {
                    title: 'Bldg_Repl_Cost_USD Sign Inversion',
                    code: 'Math.abs()',
                    desc: 'Row 142 & Row 689 inverted negative values ($1.45M, $320K) to positive replacement costs per actuarial sign validation.',
                  },
                  {
                    title: 'Postal Code & State Harmonization',
                    code: 'USPS Geo-match',
                    desc: "Re-aligned ZIP 60601 to 'IL' from broker-submitted 'IN'. Canonical centroid index updated accordingly.",
                  },
                  {
                    title: 'ISO Construction Code Normalization',
                    code: 'ISO-1 to ISO-6',
                    desc: "Re-mapped 'NC-3' and '3 - Masonry Non-Combustible' across 41 policy rows to Canonical Standard Code '3'.",
                  },
                  {
                    title: 'TIV Currency Normalization',
                    code: 'Regex Strip & Cast',
                    desc: "Stripped mixed '$' and 'USD' text tokens to numeric canonical DECIMAL(14,2) representation.",
                  },
                  {
                    title: 'Address Casing Standardization',
                    code: 'USPS Casing',
                    desc: 'Capitalized proper street titles, standard abbreviations (ST, AVE, BLVD), and stripped trailing whitespace across 12 rows.',
                  },
                ].map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg flex items-start gap-3 border border-[#D5CEBF] bg-[#F4EFE5]"
                  >
                    <div className="w-5 h-5 rounded-full flex items-center justify-center text-[#0E3B28] shrink-0 mt-0.5 bg-[#00C878]">
                      <span className="material-symbols-outlined text-[13px] font-bold">check</span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2 flex-wrap mb-1">
                        <span className="font-heading text-xs font-bold text-[#121C18]">
                          {item.title}
                        </span>
                        <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#EBE5D9] text-[#121C18] font-semibold border border-[#D5CEBF]">
                          {item.code}
                        </span>
                      </div>
                      <p className="font-sans text-[11px] text-[#4A5550] leading-normal">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-4 pt-2 flex items-center justify-between font-tag text-xs text-[#4A5550] px-3 py-2 rounded-lg border border-[#D5CEBF] bg-[#F4EFE5]">
              <span className="flex items-center gap-1.5 font-bold text-[#0E3B28]">
                <span className="material-symbols-outlined text-[16px]">verified_user</span>
                All 18 transformations strictly map to signed analyst approvals
              </span>
              <span className="font-mono text-[11px] text-[#8B9490]">v2.4.1 Engine</span>
            </div>
          </div>

          {/* Excluded / Preserved Panel */}
          <div className="rounded-xl p-5 bg-[#EBE5D9] border border-[#D5CEBF] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#D5CEBF]">
                <div className="flex items-center gap-2 flex-wrap">
                  <h2 className="font-heading text-base font-bold text-[#121C18]">
                    Not Applied / User Excluded
                  </h2>
                  <span className="px-2.5 py-0.5 rounded-full font-tag text-[11px] font-semibold bg-[#E5DEC9] text-[#4A5550] border border-[#D5CEBF]">
                    2 Excluded / Preserved
                  </span>
                </div>
                <span className="font-tag text-xs text-[#8B9490]">Immutable Raw Layer</span>
              </div>
              <p className="font-sans text-xs text-[#4A5550] mb-4">
                Explicitly rejected or ignored during review — preserved as raw data with deterministic lineage.
              </p>

              <div className="flex flex-col gap-2.5">
                <div className="p-3 rounded-lg flex items-start gap-3 border border-[#D5CEBF] bg-[#F4EFE5]">
                  <div className="w-5 h-5 rounded-full flex items-center justify-center text-[#8B9490] shrink-0 mt-0.5 bg-[#EBE5D9] border border-[#D5CEBF]">
                    <span className="material-symbols-outlined text-[13px]">block</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2 flex-wrap mb-1">
                      <span className="font-heading text-xs font-bold text-[#121C18]">
                        Future Year Built Flag (&gt;2025)
                      </span>
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#EBE5D9] text-[#4A5550] font-medium border border-[#D5CEBF]">
                        Decision: Reject / Keep As-Is
                      </span>
                    </div>
                    <p className="font-sans text-[11px] text-[#4A5550] leading-normal">
                      5 rows retained raw year built 2026-2028 per active builder-risk endorsement policy. Values passed untouched into raw metadata partition.
                    </p>
                  </div>
                </div>

                <div className="p-3 rounded-lg flex items-start gap-3 border border-[#D5CEBF] bg-[#F4EFE5]">
                  <div className="w-5 h-5 rounded-full flex items-center justify-center text-[#8B9490] shrink-0 mt-0.5 bg-[#EBE5D9] border border-[#D5CEBF]">
                    <span className="material-symbols-outlined text-[13px]">remove</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2 flex-wrap mb-1">
                      <span className="font-heading text-xs font-bold text-[#121C18]">
                        Aux_Loc_Code Custom Remap
                      </span>
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#EBE5D9] text-[#4A5550] font-medium border border-[#D5CEBF]">
                        Decision: Leave Unmapped
                      </span>
                    </div>
                    <p className="font-sans text-[11px] text-[#4A5550] leading-normal">
                      Secondary custom broker column excluded from final canonical schedule output. Preserved in Raw Source Archive without transformation.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-4 p-3.5 rounded-lg flex items-start gap-3 border border-[#D5CEBF] bg-[#F4EFE5]">
              <span className="material-symbols-outlined text-[#0E3B28] text-[20px] shrink-0 mt-0.5">
                shield
              </span>
              <div>
                <h3 className="font-heading text-xs font-bold text-[#121C18] mb-0.5">
                  Zero Silent Drops Guarantee
                </h3>
                <p className="font-sans text-[11px] text-[#4A5550] leading-relaxed">
                  All excluded items are preserved in the raw export layer and cryptographically noted in the session audit log. Nothing is ever purged or dropped without explicit signed confirmation.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Completion & Action Bar */}
        <div className="rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4 border border-[#D5CEBF] bg-[#EBE5D9]">
          <div className="flex flex-col sm:flex-row sm:items-center gap-3 text-xs font-tag">
            <div className="flex items-center gap-1.5 text-[#121C18] font-bold">
              <span className="material-symbols-outlined text-[18px] text-[#00C878]">check_circle</span>
              <span>16/17 canonical fields standardized successfully (1 unmapped field safely isolated)</span>
            </div>
            <span className="hidden sm:inline text-[#8B9490]">•</span>
            <div className="flex items-center gap-1.5 text-[#8B9490]">
              <span>SHA-256 batch hash:</span>
              <code className="font-mono text-[#121C18] px-1.5 py-0.5 rounded border border-[#D5CEBF] bg-[#F4EFE5]">
                7f9ba4e1...89c2
              </code>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto justify-end">
            <Link
              href="/worker/audit-log"
              className="px-4 py-2 rounded-full font-heading text-xs font-semibold flex items-center gap-1.5 border border-[#D5CEBF] bg-[#F4EFE5] text-[#121C18] hover:bg-[#EBE5D9] transition-colors"
            >
              <span className="material-symbols-outlined text-[16px] text-[#4A5550]">receipt_long</span>
              View Audit Event Stream
            </Link>
            <button
              type="button"
              onClick={() => router.push('/worker/output')}
              className="px-5 py-2 rounded-full font-heading text-xs font-bold transition-opacity flex items-center gap-1.5 bg-[#00C878] text-[#0E3B28] hover:bg-[#00b56c] cursor-pointer shadow-none"
            >
              <span>Continue to Output</span>
              <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>
    </WorkerShell>
  );
}
