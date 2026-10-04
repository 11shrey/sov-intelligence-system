'use client';

import React, { useState, useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import WorkerShell from '@/components/layout/WorkerShell';
import { useWorkflowStore } from '@/store/workflow-store';

const CANONICAL_TARGET_FIELDS = [
  'Property ID',
  'Building Replacement Cost',
  'Total Insurable Value',
  'Street Address',
  'City',
  'State',
  'Postal Code',
  'County',
  'Year Built',
  'Stories / Levels',
  'Square Footage',
  'Occupancy Type',
  'Construction Class',
  'Latitude',
  'Longitude',
  'Deductible (USD)',
  'Policy Limit (USD)',
  '[Select Target Field...]',
];

export default function WorkerMappingReviewPage() {
  const router = useRouter();
  const {
    mappings,
    selectedMappingId,
    setSelectedMappingId,
    acceptMapping,
    rejectMapping,
    updateMappingTarget,
    acceptAllHighConfidence,
  } = useWorkflowStore();

  const [filterTab, setFilterTab] = useState<'all' | 'needs_review' | 'low_confidence' | 'unmapped'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [inspectorNotice, setInspectorNotice] = useState<string | null>(null);

  const selectedMapping = useMemo(() => {
    return mappings.find((m) => m.id === selectedMappingId) || mappings[0];
  }, [mappings, selectedMappingId]);

  // Derived counts
  const totalCount = mappings.length;
  const mappedCount = mappings.filter((m) => m.status === 'accepted').length;
  const unmappedCount = mappings.filter((m) => m.status === 'unmapped').length;
  const needsReviewCount = mappings.filter((m) => m.status === 'needs_review' || m.status === 'proposed').length;
  const lowConfidenceCount = mappings.filter((m) => m.confidence < 85).length;

  const filteredMappings = useMemo(() => {
    return mappings.filter((m) => {
      let matchesTab = true;
      if (filterTab === 'needs_review') matchesTab = m.status === 'needs_review' || m.status === 'proposed';
      else if (filterTab === 'low_confidence') matchesTab = m.confidence < 85;
      else if (filterTab === 'unmapped') matchesTab = m.status === 'unmapped';

      const matchesSearch =
        m.sourceField.toLowerCase().includes(searchQuery.toLowerCase().trim()) ||
        m.targetCanonical.toLowerCase().includes(searchQuery.toLowerCase().trim());

      return matchesTab && matchesSearch;
    });
  }, [mappings, filterTab, searchQuery]);

  const handleTargetChange = (newTarget: string) => {
    if (!selectedMapping) return;
    updateMappingTarget(selectedMapping.id, newTarget);
    setInspectorNotice(`Rebound “${selectedMapping.sourceField}” → “${newTarget}”`);
    setTimeout(() => setInspectorNotice(null), 2500);
  };

  return (
    <WorkerShell>
      <div className="max-w-[1580px] mx-auto flex flex-col gap-5">
        {/* Breadcrumb & Header Strip */}
        <div className="flex flex-col gap-2">
          <nav className="flex items-center gap-1.5 text-[#8B9490] font-tag text-xs">
            <Link href="/worker/dashboard" className="hover:text-[#121C18]">
              SOVIA Hub
            </Link>
            <span className="material-symbols-outlined text-[13px]">chevron_right</span>
            <span>Pipeline Ingestion</span>
            <span className="material-symbols-outlined text-[13px]">chevron_right</span>
            <span className="text-[#121C18] font-semibold">Schema Mapping Review</span>
          </nav>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3.5">
              <h1 className="font-heading text-2xl sm:text-3xl font-bold text-[#121C18] leading-tight tracking-tight">
                Mapping Review
              </h1>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="inline-flex items-center px-2.5 py-1 rounded-full bg-[#D1F2DE] text-[#0E3B28] font-heading text-xs font-semibold border border-[#7FE3B0]">
                  {mappedCount}/{totalCount} Mapped
                </span>
                <span className="inline-flex items-center px-2.5 py-1 rounded-full bg-[#E5DEC9] text-[#4A5550] font-heading text-xs font-medium border border-[#D5CEBF]">
                  {unmappedCount} Unmapped
                </span>
                <span className="inline-flex items-center px-2.5 py-1 rounded-full bg-[#F7ECC8] text-[#B87A1E] font-heading text-xs font-medium border border-[#B87A1E]/40">
                  {lowConfidenceCount} Low-Confidence
                </span>
                <span className="inline-flex items-center px-2.5 py-1 rounded-full bg-[#EBE5D9] text-[#4A5550] border border-[#D5CEBF] font-heading text-xs font-medium">
                  842 Records Loaded
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              <button
                type="button"
                onClick={acceptAllHighConfidence}
                className="px-3.5 py-1.5 rounded-lg bg-[#EBE5D9] hover:bg-[#E5DEC9] border border-[#D5CEBF] text-[#0E3B28] font-heading text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                <span className="material-symbols-outlined text-[#00C878] text-[18px]">done_all</span>
                + Accept All High-Confidence (≥90%)
              </button>
            </div>
          </div>
        </div>

        {/* Filter Tabs & Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-3 bg-[#EBE5D9] p-2.5 rounded-lg border border-[#D5CEBF]">
          <div className="flex items-center gap-1.5 flex-wrap">
            <button
              type="button"
              onClick={() => setFilterTab('all')}
              className={`px-3 py-1 rounded-md text-xs font-heading font-semibold transition-colors cursor-pointer ${
                filterTab === 'all'
                  ? 'bg-[#00C878] text-[#0E3B28]'
                  : 'bg-[#F4EFE5] text-[#4A5550] border border-[#D5CEBF] hover:bg-[#EBE5D9]'
              }`}
            >
              All ({totalCount})
            </button>
            <button
              type="button"
              onClick={() => setFilterTab('needs_review')}
              className={`px-3 py-1 rounded-md text-xs font-heading font-semibold transition-colors cursor-pointer ${
                filterTab === 'needs_review'
                  ? 'bg-[#00C878] text-[#0E3B28]'
                  : 'bg-[#F4EFE5] text-[#4A5550] border border-[#D5CEBF] hover:bg-[#EBE5D9]'
              }`}
            >
              Needs Review ({needsReviewCount})
            </button>
            <button
              type="button"
              onClick={() => setFilterTab('low_confidence')}
              className={`px-3 py-1 rounded-md text-xs font-heading font-semibold transition-colors cursor-pointer ${
                filterTab === 'low_confidence'
                  ? 'bg-[#00C878] text-[#0E3B28]'
                  : 'bg-[#F4EFE5] text-[#4A5550] border border-[#D5CEBF] hover:bg-[#EBE5D9]'
              }`}
            >
              Low Confidence ({lowConfidenceCount})
            </button>
            <button
              type="button"
              onClick={() => setFilterTab('unmapped')}
              className={`px-3 py-1 rounded-md text-xs font-heading font-semibold transition-colors cursor-pointer ${
                filterTab === 'unmapped'
                  ? 'bg-[#00C878] text-[#0E3B28]'
                  : 'bg-[#F4EFE5] text-[#4A5550] border border-[#D5CEBF] hover:bg-[#EBE5D9]'
              }`}
            >
              Unmapped ({unmappedCount})
            </button>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative flex items-center">
              <span className="material-symbols-outlined text-[#8B9490] text-[16px] absolute left-2.5 pointer-events-none">
                search
              </span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter source or canonical fields..."
                className="pl-8 pr-3 py-1 rounded-md font-sans text-xs text-[#121C18] placeholder-[#8B9490] bg-[#F4EFE5] border border-[#D5CEBF] outline-none w-64 focus:border-[#00C878]"
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
            <div className="text-xs text-[#4A5550] font-heading flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#00C878]"></span>
              <span>17 Canonical Schema Slots</span>
            </div>
          </div>
        </div>

        {/* 2-Column Split: Table (65%) & Inspector (35%) */}
        <div className="grid grid-cols-12 gap-5 items-start">
          {/* Left Column: Rich Mapping Table */}
          <div className="col-span-12 xl:col-span-8 flex flex-col gap-4">
            <div className="bg-[#EBE5D9] rounded-lg border border-[#D5CEBF] overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse font-sans">
                  <thead>
                    <tr className="bg-[#EBE5D9] text-[#4A5550] uppercase tracking-wider text-[11px] font-heading font-semibold border-b border-[#D5CEBF]">
                      <th className="py-2.5 px-3 w-10 text-center">#</th>
                      <th className="py-2.5 px-3">SOURCE FIELD</th>
                      <th className="py-2.5 px-3">TARGET SCHEMA (17 CANONICAL)</th>
                      <th className="py-2.5 px-3 w-28 text-center">CONFIDENCE</th>
                      <th className="py-2.5 px-3 w-32">STATUS</th>
                      <th className="py-2.5 px-3 w-28 text-right">ACTIONS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#D5CEBF]">
                    {filteredMappings.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-8 px-4 text-center text-sm text-[#8B9490]">
                          <div className="flex flex-col items-center justify-center gap-1.5">
                            <span className="material-symbols-outlined text-[24px]">search_off</span>
                            <span>No mapping fields match the current filter.</span>
                          </div>
                        </td>
                      </tr>
                    ) : (
                      filteredMappings.map((m) => {
                        const isSelected = selectedMapping && m.id === selectedMapping.id;
                        return (
                          <tr
                            key={m.id}
                            onClick={() => setSelectedMappingId(m.id)}
                            className={`cursor-pointer transition-colors ${
                              isSelected
                                ? 'bg-[#EBE5D9] ring-2 ring-[#00C878] ring-inset'
                                : 'bg-[#F4EFE5] hover:bg-[#EBE5D9]'
                            }`}
                          >
                            <td className="py-2.5 px-3 text-center text-[11px] text-[#8B9490] font-mono">
                              {m.id < 10 ? `0${m.id}` : m.id}
                            </td>
                            <td className="py-2.5 px-3 font-mono font-semibold text-xs text-[#121C18]">
                              {m.sourceField}
                            </td>
                            <td className="py-2.5 px-3 font-heading text-xs text-[#121C18]">
                              {m.targetCanonical}
                            </td>
                            <td className="py-2.5 px-3 text-center">
                              <span
                                className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-bold ${
                                  m.confidence >= 90
                                    ? 'bg-[#D1F2DE] text-[#0E3B28]'
                                    : m.confidence >= 70
                                    ? 'bg-[#F7ECC8] text-[#B87A1E]'
                                    : 'bg-[#E5DEC9] text-[#4A5550]'
                                }`}
                              >
                                {m.confidence}%
                              </span>
                            </td>
                            <td className="py-2.5 px-3">
                              {m.status === 'accepted' ? (
                                <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#0E3B28]">
                                  <span className="material-symbols-outlined text-[15px]">verified</span>
                                  Accepted
                                </span>
                              ) : m.status === 'unmapped' ? (
                                <span className="text-[11px] font-semibold text-[#8C3B24] bg-[#FBEBE8] px-2 py-0.5 rounded border border-[#8C3B24]/30">
                                  Unmapped
                                </span>
                              ) : (
                                <span className="text-[11px] font-semibold text-[#4A5550] bg-[#E5DEC9] px-2 py-0.5 rounded border border-[#D5CEBF]">
                                  {m.status === 'needs_review' ? 'Needs Review' : 'Proposed'}
                                </span>
                              )}
                            </td>
                            <td className="py-2.5 px-3 text-right">
                              <div className="inline-flex items-center gap-1">
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    acceptMapping(m.id);
                                  }}
                                  className="p-1 rounded text-[#4A5550] hover:text-[#0E3B28] hover:bg-[#D1F2DE] transition-colors cursor-pointer"
                                  title="Accept"
                                >
                                  <span className="material-symbols-outlined text-[16px]">check</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedMappingId(m.id);
                                  }}
                                  className="p-1 rounded text-[#4A5550] hover:text-[#121C18] hover:bg-[#E5DEC9] transition-colors cursor-pointer"
                                  title="Inspect & Edit"
                                >
                                  <span className="material-symbols-outlined text-[16px]">edit</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    rejectMapping(m.id);
                                  }}
                                  className="p-1 rounded text-[#4A5550] hover:text-[#8C3B24] hover:bg-[#FBEBE8] transition-colors cursor-pointer"
                                  title="Reject / Leave Unmapped"
                                >
                                  <span className="material-symbols-outlined text-[16px]">close</span>
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>

              <div className="px-4 py-2.5 bg-[#EBE5D9] border-t border-[#D5CEBF] flex items-center justify-between text-[11px] text-[#4A5550]">
                <span className="font-mono">
                  Displaying {filteredMappings.length} of {totalCount} fields
                </span>
                <span className="font-heading">Standard schema: CRE-Actuarial-v2025.4</span>
              </div>
            </div>

            {/* Bottom Decision Toolbar */}
            <div className="w-full bg-[#EBE5D9] border border-[#D5CEBF] rounded-xl p-4 px-6 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-2 text-xs text-[#4A5550] font-heading">
                <span className="material-symbols-outlined text-[#00C878] text-[20px]">info</span>
                <span>
                  <strong>{mappedCount} fields confirmed.</strong> {totalCount - mappedCount} fields pending human validation.
                </span>
              </div>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={acceptAllHighConfidence}
                  className="px-4 py-2 rounded-lg bg-[#F4EFE5] border border-[#D5CEBF] text-[#121C18] hover:bg-[#EBE5D9] font-heading text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[17px] text-[#00C878]">done_all</span>
                  Accept All High-Confidence (≥90%)
                </button>
                <button
                  type="button"
                  onClick={() => router.push('/worker/data-quality')}
                  className="px-6 py-2.5 rounded-lg bg-[#00C878] hover:bg-[#00b56c] text-[#0E3B28] font-heading text-xs font-bold flex items-center gap-2 transition-colors cursor-pointer shadow-none"
                >
                  <span>Continue to Data Quality</span>
                  <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Mapping Inspector Panel */}
          {selectedMapping && (
            <div className="col-span-12 xl:col-span-4 bg-[#EBE5D9] border border-[#D5CEBF] rounded-xl p-5 flex flex-col gap-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#D5CEBF]">
                <div>
                  <div className="text-[11px] uppercase tracking-wider font-semibold text-[#8B9490] font-tag">
                    Field Mapping Inspector
                  </div>
                  <h2 className="font-heading text-base font-bold text-[#121C18]">
                    {selectedMapping.sourceField}
                  </h2>
                </div>
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-bold bg-[#F4EFE5] text-[#121C18] border border-[#D5CEBF]">
                  Field #{selectedMapping.id}
                </span>
              </div>

              {inspectorNotice && (
                <div className="p-2.5 rounded bg-[#D1F2DE] border border-[#7FE3B0] text-xs font-heading font-semibold text-[#0E3B28] flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px]">check_circle</span>
                  <span>{inspectorNotice}</span>
                </div>
              )}

              {/* Section 1: Source Field Profile */}
              <div className="flex flex-col gap-2">
                <div className="text-[11px] uppercase tracking-wider font-bold text-[#4A5550] font-tag">
                  1. Source Field Profile
                </div>
                <div className="bg-[#F4EFE5] p-3 rounded-lg border border-[#D5CEBF] flex flex-col gap-2.5 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="text-[#8B9490]">Source Column:</span>
                    <span className="font-mono text-xs font-bold text-[#121C18] bg-[#EBE5D9] px-2 py-0.5 rounded border border-[#D5CEBF]">
                      {selectedMapping.sourceField}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[#8B9490]">Detected Data Type:</span>
                    <span className="font-medium text-[#121C18] flex items-center gap-1">
                      <span className="material-symbols-outlined text-[#00C878] text-[15px]">data_object</span>
                      {selectedMapping.dataType}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#8B9490] block mb-1.5">Sample values from raw file:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedMapping.sampleValues.map((val, idx) => (
                        <span
                          key={idx}
                          className={`px-2 py-0.5 font-mono text-[11px] rounded border ${
                            val.includes('negative')
                              ? 'bg-[#FBEBE8] text-[#8C3B24] border-[#8C3B24]/30'
                              : 'bg-[#EBE5D9] text-[#121C18] border border-[#D5CEBF]'
                          }`}
                        >
                          {val}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Section 2: AI Recommendation & Rationale */}
              <div className="flex flex-col gap-2">
                <div className="text-[11px] uppercase tracking-wider font-bold text-[#4A5550] font-tag">
                  2. AI Recommendation &amp; Actuarial Rationale
                </div>
                <div className="bg-[#F4EFE5] p-3 rounded-lg border border-[#D5CEBF] flex flex-col gap-2.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[#8B9490]">Proposed Target:</span>
                    <span className="font-heading font-bold text-[#121C18]">
                      {selectedMapping.targetCanonical}
                    </span>
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-[#8B9490]">Confidence Score:</span>
                      <span className="font-bold text-[#0E3B28] font-mono">
                        {selectedMapping.confidence}% ({selectedMapping.confidence >= 90 ? 'High' : 'Moderate'} Confidence)
                      </span>
                    </div>
                    <div className="w-full bg-[#E5DEC9] h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-[#00C878] h-full rounded-full transition-all"
                        style={{ width: `${selectedMapping.confidence}%` }}
                      ></div>
                    </div>
                  </div>
                  <div className="bg-[#EBE5D9] p-3 rounded border border-[#D5CEBF] text-xs text-[#121C18] leading-relaxed flex gap-2">
                    <span className="material-symbols-outlined text-[#00C878] text-[18px] shrink-0 mt-0.5">
                      smart_toy
                    </span>
                    <p>{selectedMapping.reasoning}</p>
                  </div>
                </div>
              </div>

              {/* Section 3: Target Field Configuration */}
              <div className="flex flex-col gap-2">
                <div className="text-[11px] uppercase tracking-wider font-bold text-[#4A5550] font-tag">
                  3. Target Field Configuration
                </div>
                <div className="bg-[#F4EFE5] p-3 rounded-lg border border-[#D5CEBF] flex flex-col gap-2.5 text-xs">
                  <div>
                    <label className="text-[11px] font-semibold text-[#4A5550] block mb-1 font-tag">
                      Canonical Schema Field selector
                    </label>
                    <select
                      value={selectedMapping.targetCanonical}
                      onChange={(e) => handleTargetChange(e.target.value)}
                      className="w-full bg-[#EBE5D9] text-[#121C18] font-heading text-xs font-medium p-2 rounded border border-[#D5CEBF] outline-none cursor-pointer focus:border-[#00C878]"
                    >
                      {CANONICAL_TARGET_FIELDS.map((field) => (
                        <option key={field} value={field}>
                          {field}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="bg-[#E5DEC9] p-2.5 rounded border border-[#D5CEBF] flex flex-col gap-1">
                    <span className="text-[10px] uppercase font-bold text-[#4A5550] font-tag">
                      Rule applied preview:
                    </span>
                    <code className="font-mono text-[11px] text-[#0E3B28] break-all">
                      Bind raw {selectedMapping.sourceField} → {selectedMapping.targetCanonical}
                    </code>
                  </div>
                </div>
              </div>

              {/* Section 4: Actions */}
              <div className="flex flex-col gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => acceptMapping(selectedMapping.id)}
                  className="w-full py-2.5 px-4 bg-[#00C878] hover:bg-[#00b56c] text-[#0E3B28] font-heading text-xs font-bold rounded-lg flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[18px]">check_circle</span>
                  Approve Mapping (✓)
                </button>
                <button
                  type="button"
                  onClick={() => rejectMapping(selectedMapping.id)}
                  className="w-full py-2 px-4 bg-[#F4EFE5] hover:bg-[#E5DEC9] border border-[#D5CEBF] text-[#8C3B24] font-heading text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[17px]">close</span>
                  Exclude / Leave Unmapped
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </WorkerShell>
  );
}
