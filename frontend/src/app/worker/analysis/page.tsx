'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import WorkerShell from '@/components/layout/WorkerShell';
import { useWorkflowStore } from '@/store/workflow-store';

export default function WorkerAnalysisPage() {
  const router = useRouter();
  const { getActiveSession, selectedSheet } = useWorkflowStore();
  const activeSession = getActiveSession();

  const [progress, setProgress] = useState(20);
  const [isRunning, setIsRunning] = useState(true);

  useEffect(() => {
    if (!isRunning) return;

    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev < 100) return Math.min(100, prev + 8);
        clearInterval(timer);
        setIsRunning(false);
        return 100;
      });
    }, 400);

    return () => clearInterval(timer);
  }, [isRunning]);

  const handleRerun = () => {
    setProgress(15);
    setIsRunning(true);
  };

  const stage1Complete = progress >= 25;
  const stage2Complete = progress >= 55;
  const stage3Complete = progress >= 85;
  const stage4Complete = progress === 100;

  return (
    <WorkerShell>
      <div className="max-w-4xl w-full mx-auto pb-12 flex flex-col gap-6">
        {/* Header Section */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-1.5 font-tag text-xs uppercase tracking-wider text-[#8B9490]">
            <Link href="/worker/dashboard" className="hover:text-[#121C18]">
              SOVIA Hub
            </Link>
            <span className="material-symbols-outlined text-[14px]">chevron_right</span>
            <span>Pipeline Ingestion</span>
            <span className="material-symbols-outlined text-[14px]">chevron_right</span>
            <span className="text-[#4A5550] font-semibold">Real-time Inspection</span>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mt-1">
            <div>
              <h1 className="font-heading text-2xl sm:text-3xl font-bold text-[#121C18] tracking-tight">
                Analyzing Your SOV File
              </h1>
              <p className="font-sans text-sm text-[#4A5550]">
                Autonomous agents are evaluating worksheet topology, semantic field bindings, and actuarial constraints.
              </p>
            </div>
            <button
              type="button"
              onClick={handleRerun}
              className="self-start sm:self-auto inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border border-[#D5CEBF] bg-[#EBE5D9] hover:bg-[#E5DEC9] text-xs font-heading font-semibold text-[#121C18] transition-colors cursor-pointer"
            >
              <span className={`material-symbols-outlined text-[16px] ${isRunning ? 'animate-spin' : ''}`}>
                sync
              </span>
              <span>Re-run Analysis</span>
            </button>
          </div>
        </div>

        {/* Main Inspection Card */}
        <div className="bg-[#EBE5D9] rounded-xl p-6 flex flex-col gap-6 border border-[#D5CEBF]">
          {/* Card Sub-header with Session Meta */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3.5 bg-[#F4EFE5] rounded-lg border border-[#D5CEBF]">
            <div className="flex items-center gap-2.5">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-tag text-[11px] font-bold bg-[#D1F2DE] text-[#0E3B28] uppercase tracking-wider border border-[#7FE3B0]">
                <span className={`w-2 h-2 rounded-full bg-[#00C878] ${isRunning ? 'animate-pulse' : ''}`}></span>
                {isRunning ? 'Multi-Agent Pipeline Active' : 'Multi-Agent Scan Complete'}
              </span>
              <span className="font-tag text-xs text-[#8B9490]">Run ID: #AGNT-84291-CRE</span>
            </div>
            <div className="flex items-center gap-1.5 text-[#8B9490] font-tag text-xs">
              <span className="material-symbols-outlined text-[16px]">folder_zip</span>
              <span className="font-semibold text-[#121C18] truncate max-w-[220px]">
                {activeSession.fileName}
              </span>
              <span className="font-mono text-[#4A5550]">({selectedSheet || 'Property_Schedule'})</span>
            </div>
          </div>

          {/* Checklist Stages: The 4 Autonomous Agents */}
          <div className="flex flex-col gap-3">
            {/* Stage 1: Sheet Intelligence Agent */}
            <div className="flex items-start gap-4 p-4 rounded-lg bg-[#F4EFE5] border border-[#D5CEBF]">
              <div className="shrink-0 mt-0.5">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    stage1Complete
                      ? 'bg-[#00C878] text-[#0E3B28]'
                      : 'bg-[#D1F2DE] text-[#0E3B28] animate-spin'
                  }`}
                >
                  <span className="material-symbols-outlined text-[18px] font-bold">
                    {stage1Complete ? 'check' : 'sync'}
                  </span>
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <h2 className="font-heading text-[15px] text-[#121C18] font-bold leading-snug">
                      Agent 1: Sheet Intelligence
                    </h2>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full font-tag text-[10px] font-bold uppercase tracking-wider bg-[#D1F2DE] text-[#0E3B28] border border-[#7FE3B0]">
                      {stage1Complete ? 'Complete' : 'Scanning'}
                    </span>
                  </div>
                  <span className="font-tag text-xs text-[#8B9490] flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">timer</span>
                    {stage1Complete ? 'Completed in 1.4s' : 'Analyzing topology…'}
                  </span>
                </div>
                <p className="font-sans text-xs text-[#4A5550] mt-0.5">
                  3 sheets detected · ‘{selectedSheet || 'Property_Schedule'}’ isolated as primary tabular SOV (842 rows, 24 cols)
                </p>
              </div>
            </div>

            {/* Stage 2: Schema Mapping Agent */}
            <div
              className={`flex items-start gap-4 p-4 rounded-lg border transition-all ${
                stage2Complete
                  ? 'bg-[#F4EFE5] border-[#D5CEBF]'
                  : stage1Complete
                  ? 'bg-[#E5DEC9] border-[#7FE3B0]'
                  : 'bg-[#F4EFE5] border-[#D5CEBF] opacity-60'
              }`}
            >
              <div className="shrink-0 mt-0.5">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    stage2Complete
                      ? 'bg-[#00C878] text-[#0E3B28]'
                      : stage1Complete
                      ? 'bg-[#D1F2DE] text-[#0E3B28] animate-spin'
                      : 'bg-[#E5DEC9] text-[#8B9490]'
                  }`}
                >
                  <span className="material-symbols-outlined text-[18px] font-bold">
                    {stage2Complete ? 'check' : stage1Complete ? 'sync' : 'schedule'}
                  </span>
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <h2 className="font-heading text-[15px] text-[#121C18] font-bold leading-snug">
                      Agent 2: Schema Mapping
                    </h2>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full font-tag text-[10px] font-bold uppercase tracking-wider ${
                        stage2Complete
                          ? 'bg-[#D1F2DE] text-[#0E3B28] border border-[#7FE3B0]'
                          : stage1Complete
                          ? 'bg-[#F7ECC8] text-[#B87A1E] border border-[#B87A1E]'
                          : 'bg-[#E5DEC9] text-[#8B9490]'
                      }`}
                    >
                      {stage2Complete ? 'Complete' : stage1Complete ? 'Mapping' : 'Queued'}
                    </span>
                  </div>
                  <span className="font-tag text-xs text-[#8B9490] flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">timer</span>
                    {stage2Complete ? 'Completed in 2.8s' : 'Binding to 17 fields…'}
                  </span>
                </div>
                <p className="font-sans text-xs text-[#4A5550] mt-0.5">
                  15 of 17 canonical fields mapped (confidence ≥ 92%) · 2 unmapped fields flagged for human review
                </p>
              </div>
            </div>

            {/* Stage 3: Data Quality Analysis Agent */}
            <div
              className={`flex items-start gap-4 p-4 rounded-lg border transition-all ${
                stage3Complete
                  ? 'bg-[#F4EFE5] border-[#D5CEBF]'
                  : stage2Complete
                  ? 'bg-[#E5DEC9] border-[#7FE3B0]'
                  : 'bg-[#F4EFE5] border-[#D5CEBF] opacity-60'
              }`}
            >
              <div className="shrink-0 mt-0.5">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    stage3Complete
                      ? 'bg-[#00C878] text-[#0E3B28]'
                      : stage2Complete
                      ? 'bg-[#D1F2DE] text-[#0E3B28] animate-spin'
                      : 'bg-[#E5DEC9] text-[#8B9490]'
                  }`}
                >
                  <span className="material-symbols-outlined text-[18px] font-bold">
                    {stage3Complete ? 'check' : stage2Complete ? 'sync' : 'schedule'}
                  </span>
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <h2 className="font-heading text-[15px] text-[#121C18] font-bold leading-snug">
                      Agent 3: Data Quality Analysis
                    </h2>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full font-tag text-[10px] font-bold uppercase tracking-wider ${
                        stage3Complete
                          ? 'bg-[#D1F2DE] text-[#0E3B28] border border-[#7FE3B0]'
                          : stage2Complete
                          ? 'bg-[#F7ECC8] text-[#B87A1E] border border-[#B87A1E]'
                          : 'bg-[#E5DEC9] text-[#8B9490]'
                      }`}
                    >
                      {stage3Complete ? 'Complete' : stage2Complete ? 'Scanning' : 'Queued'}
                    </span>
                  </div>
                  <span className="font-tag text-xs text-[#4A5550] font-semibold flex items-center gap-1">
                    {stage3Complete ? 'Finished in 3.4s' : 'Live Scanning…'}
                  </span>
                </div>
                <p className="font-sans text-xs text-[#4A5550] font-medium mt-0.5">
                  Scanning 842 records for range violations, invalid postal codes, and negative replacement values… (5 anomalies flagged)
                </p>
                <div className="mt-2 flex flex-wrap gap-1.5 font-tag text-[11px]">
                  <span className="px-2 py-0.5 rounded bg-[#F4EFE5] text-[#121C18] border border-[#D5CEBF]">
                    Actuarial Bounds: Verified
                  </span>
                  <span className="px-2 py-0.5 rounded bg-[#F4EFE5] text-[#121C18] border border-[#D5CEBF]">
                    Geo-LatLong: 98.2%
                  </span>
                  <span className="px-2 py-0.5 rounded bg-[#D1F2DE] text-[#0E3B28] font-semibold border border-[#7FE3B0]">
                    TIV Sum Validation: Passed
                  </span>
                </div>
              </div>
            </div>

            {/* Stage 4: Transformation Planning Agent */}
            <div
              className={`flex items-start gap-4 p-4 rounded-lg border transition-all ${
                stage4Complete
                  ? 'bg-[#F4EFE5] border-[#D5CEBF]'
                  : stage3Complete
                  ? 'bg-[#E5DEC9] border-[#7FE3B0]'
                  : 'bg-[#F4EFE5] border-[#D5CEBF] opacity-60'
              }`}
            >
              <div className="shrink-0 mt-0.5">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    stage4Complete
                      ? 'bg-[#00C878] text-[#0E3B28]'
                      : stage3Complete
                      ? 'bg-[#D1F2DE] text-[#0E3B28] animate-spin'
                      : 'bg-[#E5DEC9] text-[#8B9490]'
                  }`}
                >
                  <span className="material-symbols-outlined text-[18px] font-bold">
                    {stage4Complete ? 'check' : stage3Complete ? 'sync' : 'schedule'}
                  </span>
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <h2 className="font-heading text-[15px] text-[#121C18] font-bold leading-snug">
                      Agent 4: Transformation Planning
                    </h2>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full font-tag text-[10px] font-bold uppercase tracking-wider ${
                        stage4Complete
                          ? 'bg-[#D1F2DE] text-[#0E3B28] border border-[#7FE3B0]'
                          : stage3Complete
                          ? 'bg-[#F7ECC8] text-[#B87A1E] border border-[#B87A1E]'
                          : 'bg-[#E5DEC9] text-[#8B9490]'
                      }`}
                    >
                      {stage4Complete ? 'Ready' : stage3Complete ? 'Generating' : 'Queued'}
                    </span>
                  </div>
                  <span className="font-tag text-xs text-[#8B9490] uppercase tracking-wider">
                    {stage4Complete ? 'Plan Locked' : 'Synthesizing rules'}
                  </span>
                </div>
                <p className="font-sans text-xs text-[#4A5550] mt-0.5">
                  Deterministic change rules prepared: Currency casting, USPS geocoding, ISO construction classification.
                </p>
              </div>
            </div>
          </div>

          {/* Execution Progress */}
          <div className="pt-2 flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 font-tag text-[#8B9490]">
                <span className="font-medium text-[#121C18]">Pipeline Overall</span>
                <span>·</span>
                <span>Est. remaining: ~{progress === 100 ? '0' : '1.5'}s</span>
                <span>·</span>
                <span>0 unapproved writes</span>
              </div>
              <span className="font-heading text-[14px] font-bold text-[#0E3B28]">
                {progress}% Complete
              </span>
            </div>
            <div className="w-full h-2.5 rounded-full bg-[#E5DEC9] overflow-hidden border border-[#D5CEBF]">
              <div
                className="h-full bg-[#00C878] rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>

          {/* Controls & Actions */}
          <div className="flex flex-col-reverse sm:flex-row items-center justify-between gap-4 pt-2 border-t border-[#D5CEBF]">
            <div className="flex items-center gap-2 text-[#8B9490] font-tag text-xs">
              <span className="material-symbols-outlined text-[16px] text-[#0E3B28]">shield</span>
              <span>Deterministic execution sandboxed under ISO-27001 policy</span>
            </div>
            <div className="flex items-center gap-2.5 w-full sm:w-auto justify-end">
              <button
                type="button"
                onClick={() => router.push('/worker/mapping-review')}
                className="w-full sm:w-auto px-6 py-2.5 rounded-full font-heading text-xs font-bold text-[#0E3B28] bg-[#00C878] hover:bg-[#00b56c] transition-colors flex items-center justify-center gap-1.5 cursor-pointer shadow-none"
              >
                <span>{progress === 100 ? 'Continue to Mapping Review' : 'Skip to Mapping Review'}</span>
                <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
              </button>
            </div>
          </div>
        </div>

        {/* Real-time Agent Log Stream */}
        <div className="bg-[#EBE5D9] rounded-xl p-4 border border-[#D5CEBF]">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#0E3B28] text-[16px]">terminal</span>
              <span className="font-tag text-xs uppercase tracking-wider text-[#0E3B28] font-bold">
                Live Telemetry Stream
              </span>
            </div>
            <span className="font-tag text-[11px] text-[#8B9490]">Live Multi-Agent Event Bus</span>
          </div>
          <div className="bg-[#F4EFE5] rounded-lg p-3 font-mono text-[11px] text-[#4A5550] flex flex-col gap-1 border border-[#D5CEBF] leading-relaxed">
            <div>[00:01.402] Sheet_Intel_Agent: isolated sheet “{selectedSheet || 'Property_Schedule'}” (dimensions: 842 x 24)</div>
            {progress >= 40 && (
              <div>[00:02.811] Schema_Mapping_Agent: mapped 15 fields into canonical CRE-v2025 dictionary</div>
            )}
            {progress >= 70 && (
              <div>[00:03.119] Data_Quality_Agent: scanned columns “Bldg_Repl_Cost”, “Postal_Code”, “Yr_Built” (5 flagged)</div>
            )}
            {progress >= 95 && (
              <div className="text-[#0E3B28] font-semibold">
                [00:03.490] Transform_Planning_Agent: deterministic rule matrix verified against RMS/AIR standard
              </div>
            )}
          </div>
        </div>
      </div>
    </WorkerShell>
  );
}
