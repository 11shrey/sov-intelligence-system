'use client';

import React, { useState, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import WorkerShell from '@/components/layout/WorkerShell';
import { useWorkflowStore } from '@/store/workflow-store';

interface StagedFile {
  name: string;
  size: string;
  sheetCount: number;
  status: string;
}

export default function WorkerUploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { selectedSheet, setSelectedSheet } = useWorkflowStore();
  const [sheet, setSheet] = useState(selectedSheet || 'Property_Schedule');

  const [stagedFile, setStagedFile] = useState<StagedFile | null>({
    name: 'Property_SOV_Jan.xlsx',
    size: '14.2 MB',
    sheetCount: 3,
    status: 'Uploaded & Scanned by Sheet Intelligence',
  });

  const [scanNotice, setScanNotice] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
    setStagedFile({
      name: file.name,
      size: `${sizeMb} MB`,
      sheetCount: 3,
      status: 'Analyzing worksheet topology...',
    });

    setScanNotice(`Sheet Intelligence Agent analyzing ${file.name}...`);
    setTimeout(() => {
      setStagedFile((prev) =>
        prev
          ? {
              ...prev,
              status: 'Uploaded & Scanned by Sheet Intelligence',
            }
          : null
      );
      setScanNotice(`Sheet Intelligence scan complete: 3 schedules identified.`);
      setTimeout(() => setScanNotice(null), 3000);
    }, 800);
  };

  const handleContinue = () => {
    setSelectedSheet(sheet);
    router.push('/worker/analysis');
  };

  const handleClearFile = () => {
    setStagedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <WorkerShell>
      <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto pb-12">
        {/* Breadcrumb & Header */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-1.5 text-[#8B9490] font-tag text-xs">
            <Link href="/worker/dashboard" className="hover:text-[#121C18] cursor-pointer">
              SOVIA Hub
            </Link>
            <span>/</span>
            <span className="text-[#4A5550] font-medium">Upload SOV</span>
          </div>
          <div className="flex flex-wrap items-baseline justify-between gap-4 mt-1">
            <div>
              <h1 className="font-heading text-2xl sm:text-3xl font-bold text-[#121C18] tracking-tight">
                Upload SOV
              </h1>
              <p className="font-sans text-sm text-[#4A5550] mt-1">
                Ingest Statement of Values workbook and select target schedule for multi-agent extraction.
              </p>
            </div>
            <div className="flex items-center gap-2 bg-[#EBE5D9] px-3.5 py-1.5 rounded-full border border-[#D5CEBF]">
              <span className="inline-block w-2 h-2 rounded-full bg-[#00C878]"></span>
              <span className="font-tag text-xs text-[#0E3B28] font-semibold">
                Sheet Intelligence Agent Active
              </span>
              <span className="text-[#D5CEBF]">·</span>
              <span className="font-tag text-xs text-[#8B9490]">v2.4 Canonical</span>
            </div>
          </div>
        </div>

        {/* Scan notice banner */}
        {scanNotice && (
          <div className="p-3 bg-[#D1F2DE] border border-[#7FE3B0] rounded-xl text-xs font-heading font-semibold text-[#0E3B28] flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#00C878] animate-ping"></span>
            <span>{scanNotice}</span>
          </div>
        )}

        {/* Upload File Card & Dropzone */}
        <div className="flex flex-col gap-4">
          {stagedFile ? (
            <div className="bg-[#EBE5D9] rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 border border-[#D5CEBF]">
              <div className="flex items-center gap-4 min-w-0">
                <div className="w-12 h-12 rounded-lg bg-[#E5DEC9] border border-[#D5CEBF] flex items-center justify-center shrink-0 text-[#0E3B28]">
                  <span className="material-symbols-outlined text-[28px]">description</span>
                </div>
                <div className="flex flex-col min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-heading text-[15px] font-bold text-[#121C18] truncate">
                      {stagedFile.name}
                    </span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full font-tag text-[11px] bg-[#E5DEC9] text-[#4A5550] font-medium border border-[#D5CEBF]">
                      {stagedFile.name.endsWith('.csv') ? 'CSV' : 'XLSX'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5 text-[#4A5550] font-sans text-xs flex-wrap">
                    <span>{stagedFile.size}</span>
                    <span>·</span>
                    <span>{stagedFile.sheetCount} Sheets Detected</span>
                    <span>·</span>
                    <div className="flex items-center gap-1 text-[#00C878] font-semibold">
                      <span className="material-symbols-outlined text-[16px]">check_circle</span>
                      <span>{stagedFile.status}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full font-heading text-xs font-semibold text-[#121C18] bg-[#F4EFE5] border border-[#D5CEBF] hover:bg-[#EBE5D9] transition-colors cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[16px]">swap_horiz</span>
                  Replace file
                </button>
                <button
                  type="button"
                  onClick={handleClearFile}
                  aria-label="Delete staged file"
                  className="inline-flex items-center justify-center w-9 h-9 rounded-full text-[#8C3B24] hover:bg-[#FBEBE8] transition-colors cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[20px]">delete</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-[#EBE5D9] rounded-xl p-6 text-center border border-[#D5CEBF] flex flex-col items-center justify-center gap-2">
              <span className="material-symbols-outlined text-[32px] text-[#8B9490]">upload_file</span>
              <p className="font-heading text-sm font-semibold text-[#121C18]">
                No SOV workbook currently staged.
              </p>
              <p className="font-sans text-xs text-[#8B9490]">
                Upload or select a file below to begin Sheet Intelligence inspection.
              </p>
            </div>
          )}

          {/* Drag & Drop Area */}
          <div
            onClick={() => fileInputRef.current?.click()}
            className="relative bg-[#EBE5D9] rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer border border-dashed border-[#D5CEBF] hover:border-[#00C878] transition-colors group"
          >
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileChange}
              accept=".xlsx,.xls,.csv"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div className="w-12 h-12 rounded-full bg-[#F4EFE5] border border-[#D5CEBF] flex items-center justify-center text-[#8B9490] group-hover:text-[#00C878] group-hover:border-[#00C878] transition-colors mb-2">
              <span className="material-symbols-outlined text-[26px]">cloud_upload</span>
            </div>
            <p className="font-heading text-[15px] font-bold text-[#121C18]">
              Drag &amp; drop an SOV workbook here or click to browse
            </p>
            <p className="font-sans text-xs text-[#8B9490] mt-1 max-w-xl">
              Supported formats: .xlsx, .xls, .csv · Maximum file size: 50 MB · 256-bit encrypted pipeline
            </p>
          </div>
        </div>

        {/* Detected Sheets Section */}
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-heading text-lg font-bold text-[#121C18]">Detected Sheets (3)</h2>
                <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-[#E5DEC9] text-[#0E3B28] font-tag text-xs font-bold border border-[#D5CEBF]">
                  3
                </span>
              </div>
              <p className="font-sans text-xs text-[#4A5550] mt-1">
                Select the primary Statement of Values schedule to bind to the 17-canonical schema. Auxiliary sheets will be parsed for contextual metadata.
              </p>
            </div>
            <div className="flex items-center gap-3 font-tag text-xs text-[#8B9490]">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#00C878]"></span>
                Target Canonical Primary
              </span>
              <span>·</span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#8B9490]"></span>
                Auxiliary Notes
              </span>
            </div>
          </div>

          <div className="flex flex-col gap-2.5">
            {/* Sheet 1: Property_Schedule (Recommended) */}
            <div
              onClick={() => setSheet('Property_Schedule')}
              className={`group relative flex items-start gap-4 p-4 rounded-xl cursor-pointer transition-all border ${
                sheet === 'Property_Schedule'
                  ? 'bg-[#EBE5D9] border-[#00C878] ring-1 ring-[#00C878]'
                  : 'bg-[#F4EFE5] border-[#D5CEBF] hover:bg-[#EBE5D9]'
              }`}
            >
              <div className="pt-0.5">
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center border ${
                    sheet === 'Property_Schedule'
                      ? 'bg-[#00C878] border-[#00C878]'
                      : 'bg-transparent border-[#D5CEBF]'
                  }`}
                >
                  {sheet === 'Property_Schedule' && (
                    <div className="w-2 h-2 rounded-full bg-[#0E3B28]"></div>
                  )}
                </div>
              </div>
              <div className="flex-1 min-w-0 flex flex-col gap-1">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-heading text-[15px] font-bold text-[#121C18] tracking-tight">
                      Property_Schedule
                    </span>
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-tag text-[11px] bg-[#D1F2DE] text-[#0E3B28] font-bold border border-[#7FE3B0]">
                      <span className="material-symbols-outlined text-[13px]">verified</span>
                      SOV (Recommended)
                    </span>
                  </div>
                  <div className="flex items-center gap-1 font-tag text-xs text-[#0E3B28] font-semibold">
                    <span className="material-symbols-outlined text-[15px]">grid_on</span>
                    <span>Tabular Confidence 99.4%</span>
                  </div>
                </div>
                <div className="font-sans text-xs text-[#4A5550] flex flex-wrap items-center gap-2">
                  <span className="font-bold text-[#121C18]">842 rows × 24 columns</span>
                  <span className="text-[#8B9490]">·</span>
                  <span>Validated Tabular Structure</span>
                  <span className="text-[#8B9490]">·</span>
                  <span className="text-[#8B9490] truncate">
                    Contains: Bldg Repl Cost, Year Built, ISO Code, Address, TIV, Deductible
                  </span>
                </div>
                <div className="mt-1 pt-1 flex flex-wrap items-center gap-1.5">
                  <span className="font-tag text-[10px] text-[#8B9490] uppercase tracking-wider font-semibold">
                    Detected Columns:
                  </span>
                  {['Loc #', 'Street_Address', 'Building_Value', 'Contents_Value', 'Const_Type', '+19 more'].map(
                    (col) => (
                      <span
                        key={col}
                        className="px-2 py-0.5 rounded text-[#4A5550] font-tag text-[11px] bg-[#F4EFE5] border border-[#D5CEBF]"
                      >
                        {col}
                      </span>
                    )
                  )}
                </div>
              </div>
            </div>

            {/* Sheet 2: Summary_Portfolio_Notes */}
            <div
              onClick={() => setSheet('Summary_Portfolio_Notes')}
              className={`group relative flex items-start gap-4 p-4 rounded-xl cursor-pointer transition-all border ${
                sheet === 'Summary_Portfolio_Notes'
                  ? 'bg-[#EBE5D9] border-[#00C878] ring-1 ring-[#00C878]'
                  : 'bg-[#F4EFE5] border-[#D5CEBF] hover:bg-[#EBE5D9]'
              }`}
            >
              <div className="pt-0.5">
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center border ${
                    sheet === 'Summary_Portfolio_Notes'
                      ? 'bg-[#00C878] border-[#00C878]'
                      : 'bg-transparent border-[#D5CEBF]'
                  }`}
                >
                  {sheet === 'Summary_Portfolio_Notes' && (
                    <div className="w-2 h-2 rounded-full bg-[#0E3B28]"></div>
                  )}
                </div>
              </div>
              <div className="flex-1 min-w-0 flex flex-col gap-1">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-heading text-[15px] font-bold text-[#121C18]">
                      Summary_Portfolio_Notes
                    </span>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full font-tag text-[11px] bg-[#E5DEC9] text-[#4A5550] border border-[#D5CEBF]">
                      Auxiliary Notes
                    </span>
                  </div>
                  <span className="font-tag text-xs text-[#8B9490]">Non-tabular text block</span>
                </div>
                <div className="font-sans text-xs text-[#4A5550] flex flex-wrap items-center gap-2">
                  <span>0 data rows × 8 columns</span>
                  <span className="text-[#8B9490]">·</span>
                  <span>Form guidelines only</span>
                  <span className="text-[#8B9490]">·</span>
                  <span className="text-[#8B9490] truncate">Contains broker underwriting footnotes</span>
                </div>
              </div>
            </div>

            {/* Sheet 3: Locations_Geo_Ref */}
            <div
              onClick={() => setSheet('Locations_Geo_Ref')}
              className={`group relative flex items-start gap-4 p-4 rounded-xl cursor-pointer transition-all border ${
                sheet === 'Locations_Geo_Ref'
                  ? 'bg-[#EBE5D9] border-[#00C878] ring-1 ring-[#00C878]'
                  : 'bg-[#F4EFE5] border-[#D5CEBF] hover:bg-[#EBE5D9]'
              }`}
            >
              <div className="pt-0.5">
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center border ${
                    sheet === 'Locations_Geo_Ref'
                      ? 'bg-[#00C878] border-[#00C878]'
                      : 'bg-transparent border-[#D5CEBF]'
                  }`}
                >
                  {sheet === 'Locations_Geo_Ref' && (
                    <div className="w-2 h-2 rounded-full bg-[#0E3B28]"></div>
                  )}
                </div>
              </div>
              <div className="flex-1 min-w-0 flex flex-col gap-1">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-heading text-[15px] font-bold text-[#121C18]">
                      Locations_Geo_Ref
                    </span>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full font-tag text-[11px] bg-[#E5DEC9] text-[#4A5550] border border-[#D5CEBF]">
                      Geo Lookup Table
                    </span>
                  </div>
                  <span className="font-tag text-xs text-[#8B9490]">Auxiliary Reference</span>
                </div>
                <div className="font-sans text-xs text-[#4A5550] flex flex-wrap items-center gap-2">
                  <span>18 rows × 6 columns</span>
                  <span className="text-[#8B9490]">·</span>
                  <span>Centroid Coordinates</span>
                  <span className="text-[#8B9490]">·</span>
                  <span className="text-[#8B9490] truncate">USPS FIPS &amp; County lookup indices</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Banner & Continue Action */}
        <div className="bg-[#EBE5D9] rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 border border-[#D5CEBF]">
          <div className="flex items-center gap-2.5 max-w-xl min-w-0">
            <span className="material-symbols-outlined text-[#0E3B28] shrink-0 text-[20px]">
              info
            </span>
            <p className="font-sans text-xs text-[#4A5550] leading-snug">
              Sheet Intelligence Agent will isolate tabular headers on ‘{sheet}’ and launch 17-field canonical mapping on continuation.
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Link
              href="/worker/dashboard"
              className="px-5 py-2 rounded-full font-heading text-xs font-semibold text-[#4A5550] bg-[#F4EFE5] border border-[#D5CEBF] hover:bg-[#EBE5D9] transition-colors"
            >
              Cancel
            </Link>
            <button
              type="button"
              onClick={handleContinue}
              className="inline-flex items-center gap-1 px-6 py-2 rounded-full font-heading text-xs font-bold text-[#0E3B28] bg-[#00C878] hover:bg-[#00b56c] transition-colors cursor-pointer shadow-none"
            >
              <span>Continue to Analysis</span>
              <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>
    </WorkerShell>
  );
}
