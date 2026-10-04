import React from 'react';
import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-[#F4EFE5] text-[#121C18] selection:bg-[#7FE3B0] selection:text-[#0E3B28]">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-50 w-full bg-[#F4EFE5] border-b border-[#D5CEBF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          {/* Brand Logo & Identity */}
          <Link href="/" className="flex items-center gap-3.5 group text-left">
            <div className="w-10 h-10 rounded-full bg-[#0E3B28] flex items-center justify-center text-[#00C878] font-bold text-lg">
              S
            </div>
            <div className="flex flex-col">
              <span className="text-2xl font-bold tracking-tight text-[#121C18] group-hover:text-[#3F6B52] transition-colors">
                SOVIA
              </span>
              <span className="text-[9px] tracking-wider uppercase font-tag text-[#8B9490] font-medium">
                Autonomous Risk Cleansing
              </span>
            </div>
          </Link>

          {/* Central Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-[#121C18]">
            <a className="hover:text-[#3F6B52] transition-colors" href="#how-it-works">
              How it Works
            </a>
            <a className="hover:text-[#3F6B52] transition-colors" href="#features">
              Features
            </a>
            <a className="hover:text-[#3F6B52] transition-colors" href="#architecture">
              Architecture
            </a>
            <a className="hover:text-[#3F6B52] transition-colors" href="#governance">
              Security &amp; Governance
            </a>
          </nav>

          {/* Action Buttons */}
          <div className="flex items-center gap-4">
            <Link
              className="font-medium text-sm text-[#4A5550] hover:text-[#121C18] transition-colors mr-2"
              href="/signin"
            >
              Sign In
            </Link>
            <Link
              className="inline-flex items-center justify-center bg-[#00C878] text-[#0E3B28] font-bold text-sm px-6 py-2.5 rounded-full hover:bg-[#00b56c] transition-colors"
              href="/signin"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="py-16 md:py-24 border-b border-[#D5CEBF] bg-[#F4EFE5]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
              {/* Hero Left Column */}
              <div className="lg:col-span-6 flex flex-col items-start">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#D1F2DE] border border-[#7FE3B0] text-[#0E3B28] text-xs font-tag tracking-wider uppercase font-semibold mb-6">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#0E3B28]"></span>
                  Enterprise SOV Pipeline
                </div>

                <h1 className="text-4xl sm:text-5xl lg:text-[52px] font-bold text-[#121C18] tracking-tight leading-[1.15] mb-6">
                  AI agents for cleaner, smarter, and more reliable SOV data.
                </h1>

                <p className="text-base sm:text-lg text-[#4A5550] font-sans leading-relaxed mb-8 max-w-xl">
                  Automate Statement of Values ingestion, 17-canonical schema mapping, and catastrophic risk validation with human-governed agentic workflows.
                </p>

                <div className="flex flex-wrap items-center gap-4 w-full sm:w-auto mb-10">
                  <Link
                    className="w-full sm:w-auto text-center bg-[#00C878] hover:bg-[#00b56c] text-[#0E3B28] font-bold text-sm px-8 py-3.5 rounded-full transition-colors"
                    href="/signin"
                  >
                    Start Analysis
                  </Link>
                  <a
                    className="w-full sm:w-auto text-center border-[1.5px] border-[#3F6B52] text-[#0E3B28] hover:bg-[#EBE5D9] font-semibold text-sm px-8 py-3.5 rounded-full transition-colors"
                    href="#how-it-works"
                  >
                    Watch Demo
                  </a>
                </div>

                {/* Proof Chips */}
                <div className="flex flex-wrap items-center gap-y-3 gap-x-6 pt-4 border-t border-[#D5CEBF] w-full text-xs font-tag text-[#8B9490]">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-[#121C18] font-heading">4</span>
                    <span>Autonomous Agents</span>
                  </div>
                  <span className="hidden sm:inline-block text-[#D5CEBF]">•</span>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-[#121C18] font-heading">17</span>
                    <span>Standard Risk Fields</span>
                  </div>
                  <span className="hidden sm:inline-block text-[#D5CEBF]">•</span>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-[#121C18] font-heading">100%</span>
                    <span>Tamper-Evident Audit Trail</span>
                  </div>
                </div>
              </div>

              {/* Hero Right Column: Mockup Table */}
              <div className="lg:col-span-6 w-full">
                <div className="rounded-xl overflow-hidden border border-[#D5CEBF] bg-[#EBE5D9]">
                  <div className="px-5 py-3.5 border-b border-[#D5CEBF] bg-[#E5DEC9] flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#00C878]"></span>
                      <span className="text-xs font-mono font-semibold text-[#121C18] uppercase tracking-wider">
                        SOVIA Schema Mapping Preview
                      </span>
                    </div>
                    <span className="text-[11px] font-tag font-semibold px-2 py-0.5 rounded bg-[#D1F2DE] text-[#0E3B28] border border-[#7FE3B0]">
                      Zero Unapproved Writes
                    </span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-[#EBE5D9] border-b border-[#D5CEBF] text-[#8B9490] font-tag uppercase tracking-wider">
                        <tr>
                          <th className="py-2.5 px-4 font-semibold">Raw Broker Column</th>
                          <th className="py-2.5 px-4 font-semibold">Canonical Target (17)</th>
                          <th className="py-2.5 px-4 font-semibold text-right">Confidence</th>
                          <th className="py-2.5 px-4 font-semibold text-center">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#D5CEBF] text-[#121C18] font-mono">
                        <tr className="hover:bg-[#F4EFE5]/50">
                          <td className="py-3 px-4 text-[#4A5550]">Bldg Repl Cost</td>
                          <td className="py-3 px-4 font-medium text-[#0E3B28]">building_replacement_cost</td>
                          <td className="py-3 px-4 text-right">
                            <span className="inline-block px-1.5 py-0.5 rounded bg-[#D1F2DE] text-[#0E3B28] font-semibold text-[11px]">
                              94%
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span className="inline-flex items-center text-[10px] text-[#0E3B28] font-sans font-semibold px-2 py-0.5 rounded-full bg-[#D1F2DE] border border-[#7FE3B0]">
                              Bound
                            </span>
                          </td>
                        </tr>
                        <tr className="hover:bg-[#F4EFE5]/50">
                          <td className="py-3 px-4 text-[#4A5550]">Yr Built</td>
                          <td className="py-3 px-4 font-medium text-[#0E3B28]">year_built</td>
                          <td className="py-3 px-4 text-right">
                            <span className="inline-block px-1.5 py-0.5 rounded bg-[#D1F2DE] text-[#0E3B28] font-semibold text-[11px]">
                              98%
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span className="inline-flex items-center text-[10px] text-[#0E3B28] font-sans font-semibold px-2 py-0.5 rounded-full bg-[#D1F2DE] border border-[#7FE3B0]">
                              Bound
                            </span>
                          </td>
                        </tr>
                        <tr className="hover:bg-[#F4EFE5]/50">
                          <td className="py-3 px-4 text-[#4A5550]">ISO Const Class</td>
                          <td className="py-3 px-4 font-medium text-[#0E3B28]">construction_code_iso</td>
                          <td className="py-3 px-4 text-right">
                            <span className="inline-block px-1.5 py-0.5 rounded bg-[#D1F2DE] text-[#0E3B28] font-semibold text-[11px]">
                              91%
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span className="inline-flex items-center text-[10px] text-[#0E3B28] font-sans font-semibold px-2 py-0.5 rounded-full bg-[#D1F2DE] border border-[#7FE3B0]">
                              Bound
                            </span>
                          </td>
                        </tr>
                        <tr className="hover:bg-[#F4EFE5]/50">
                          <td className="py-3 px-4 text-[#4A5550]">Occ Description</td>
                          <td className="py-3 px-4 font-medium text-[#0E3B28]">occupancy_type_sic</td>
                          <td className="py-3 px-4 text-right">
                            <span className="inline-block px-1.5 py-0.5 rounded bg-[#D1F2DE] text-[#0E3B28] font-semibold text-[11px]">
                              89%
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span className="inline-flex items-center text-[10px] text-[#B87A1E] font-sans font-semibold px-2 py-0.5 rounded-full bg-[#F7ECC8] border border-[#B87A1E]">
                              Review
                            </span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <div className="px-5 py-3 border-t border-[#D5CEBF] bg-[#E5DEC9] flex items-center justify-between text-xs text-[#4A5550]">
                    <span className="flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[#00C878] text-[18px]">verified</span>
                      Deterministic Actuarial Schema Validated
                    </span>
                    <span className="font-tag text-[#8B9490] text-[11px]">Audit Hash: #963b-sov</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="py-20 bg-[#F4EFE5] border-b border-[#D5CEBF]" id="how-it-works">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="max-w-2xl mb-16 text-left">
              <span className="text-xs font-tag tracking-wider uppercase text-[#3F6B52] font-semibold mb-2 block">
                Methodology
              </span>
              <h2 className="text-3xl font-bold tracking-tight text-[#121C18] mb-4">How It Works</h2>
              <p className="text-[#4A5550] font-sans text-base">
                A hardened 4-step pipeline designed for underwriting teams. Transition unstructured broker tables into high-fidelity modeled exposures in minutes.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {/* Step 1 */}
              <div className="flex flex-col bg-[#EBE5D9] p-6 rounded-xl border border-[#D5CEBF]">
                <div className="flex items-center gap-4 mb-5">
                  <div className="w-12 h-12 rounded-full bg-[#D1F2DE] border border-[#7FE3B0] flex items-center justify-center shrink-0">
                    <span className="font-tag font-bold text-[#0E3B28] text-sm">01</span>
                  </div>
                  <span className="text-xs font-tag tracking-widest text-[#8B9490] uppercase font-semibold">
                    Ingestion
                  </span>
                </div>
                <h3 className="text-lg font-bold text-[#121C18] mb-2 font-heading">Upload SOV</h3>
                <p className="text-sm text-[#4A5550] leading-relaxed font-sans">
                  Ingest complex multi-tab commercial workbooks (.xlsx, .xls, .csv) with irregular nested headers and merged cell zones.
                </p>
              </div>

              {/* Step 2 */}
              <div className="flex flex-col bg-[#EBE5D9] p-6 rounded-xl border border-[#D5CEBF]">
                <div className="flex items-center gap-4 mb-5">
                  <div className="w-12 h-12 rounded-full bg-[#D1F2DE] border border-[#7FE3B0] flex items-center justify-center shrink-0">
                    <span className="font-tag font-bold text-[#0E3B28] text-sm">02</span>
                  </div>
                  <span className="text-xs font-tag tracking-widest text-[#8B9490] uppercase font-semibold">
                    Inspection
                  </span>
                </div>
                <h3 className="text-lg font-bold text-[#121C18] mb-2 font-heading">Analyze</h3>
                <p className="text-sm text-[#4A5550] leading-relaxed font-sans">
                  Autonomous Sheet Intelligence &amp; Schema Mapping agents isolate property schedules and evaluate messy row headers.
                </p>
              </div>

              {/* Step 3 */}
              <div className="flex flex-col bg-[#EBE5D9] p-6 rounded-xl border border-[#D5CEBF]">
                <div className="flex items-center gap-4 mb-5">
                  <div className="w-12 h-12 rounded-full bg-[#D1F2DE] border border-[#7FE3B0] flex items-center justify-center shrink-0">
                    <span className="font-tag font-bold text-[#0E3B28] text-sm">03</span>
                  </div>
                  <span className="text-xs font-tag tracking-widest text-[#8B9490] uppercase font-semibold">
                    Governance
                  </span>
                </div>
                <h3 className="text-lg font-bold text-[#121C18] mb-2 font-heading">Review &amp; Govern</h3>
                <p className="text-sm text-[#4A5550] leading-relaxed font-sans">
                  Underwriters approve, rebind, or reject field targets with confidence scores and explainable semantic reasoning.
                </p>
              </div>

              {/* Step 4 */}
              <div className="flex flex-col bg-[#EBE5D9] p-6 rounded-xl border border-[#D5CEBF]">
                <div className="flex items-center gap-4 mb-5">
                  <div className="w-12 h-12 rounded-full bg-[#D1F2DE] border border-[#7FE3B0] flex items-center justify-center shrink-0">
                    <span className="font-tag font-bold text-[#0E3B28] text-sm">04</span>
                  </div>
                  <span className="text-xs font-tag tracking-widest text-[#8B9490] uppercase font-semibold">
                    Execution
                  </span>
                </div>
                <h3 className="text-lg font-bold text-[#121C18] mb-2 font-heading">Transform &amp; Export</h3>
                <p className="text-sm text-[#4A5550] leading-relaxed font-sans">
                  Export cleaned, normalized schedules directly to RMS RiskLink, AIR, or EDM schemas with a cryptographic audit trail.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Core Capabilities */}
        <section className="py-20 bg-[#F4EFE5] border-b border-[#D5CEBF]" id="features">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="max-w-2xl mb-14 text-left">
              <span className="text-xs font-tag tracking-wider uppercase text-[#3F6B52] font-semibold mb-2 block">
                Core Capabilities
              </span>
              <h2 className="text-3xl font-bold tracking-tight text-[#121C18] mb-3">
                Engineered for Underwriting Precision
              </h2>
              <p className="text-[#4A5550] font-sans text-base">
                Generic LLMs hallucinate critical risk values. SOVIA pairs deterministic actuarial models with governed multi-agent intelligence.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <article className="bg-[#EBE5D9] p-8 rounded-xl border border-[#D5CEBF]">
                <div className="w-12 h-12 rounded-lg bg-[#D1F2DE] border border-[#7FE3B0] flex items-center justify-center text-[#0E3B28] mb-6">
                  <span className="material-symbols-outlined text-[24px]">grid_view</span>
                </div>
                <h3 className="text-xl font-bold text-[#121C18] mb-3 font-heading">
                  Sheet Intelligence Agent
                </h3>
                <p className="text-[#4A5550] text-sm leading-relaxed font-sans">
                  Auto-detects and isolates true property schedules across complex workbooks while silently filtering out summary tabs, pivot dumps, broker notes, and corrupted header noise.
                </p>
              </article>

              <article className="bg-[#EBE5D9] p-8 rounded-xl border border-[#D5CEBF]">
                <div className="w-12 h-12 rounded-lg bg-[#D1F2DE] border border-[#7FE3B0] flex items-center justify-center text-[#0E3B28] mb-6">
                  <span className="material-symbols-outlined text-[24px]">hub</span>
                </div>
                <h3 className="text-xl font-bold text-[#121C18] mb-3 font-heading">
                  17 Canonical Schema Bindings
                </h3>
                <p className="text-[#4A5550] text-sm leading-relaxed font-sans">
                  Deterministic semantic models bind messy non-standard broker aliases directly to canonical RMS, AIR, and custom insurer exposure schemas with explicit confidence scoring.
                </p>
              </article>

              <article className="bg-[#EBE5D9] p-8 rounded-xl border border-[#D5CEBF]">
                <div className="w-12 h-12 rounded-lg bg-[#D1F2DE] border border-[#7FE3B0] flex items-center justify-center text-[#0E3B28] mb-6">
                  <span className="material-symbols-outlined text-[24px]">verified</span>
                </div>
                <h3 className="text-xl font-bold text-[#121C18] mb-3 font-heading">
                  Actuarial Data Quality Scan
                </h3>
                <p className="text-[#4A5550] text-sm leading-relaxed font-sans">
                  Flags negative replacement values, impossible square footages, year-built typos, and state/postal code mismatches prior to catastrophe modeling ingestion.
                </p>
              </article>

              <article className="bg-[#EBE5D9] p-8 rounded-xl border border-[#D5CEBF]">
                <div className="w-12 h-12 rounded-lg bg-[#D1F2DE] border border-[#7FE3B0] flex items-center justify-center text-[#0E3B28] mb-6">
                  <span className="material-symbols-outlined text-[24px]">shield</span>
                </div>
                <h3 className="text-xl font-bold text-[#121C18] mb-3 font-heading">
                  Zero Unapproved Writes
                </h3>
                <p className="text-[#4A5550] text-sm leading-relaxed font-sans">
                  A hardened statutory governance barrier where autonomous agents propose cell corrections and bindings, but underwriters retain absolute veto and change authorization.
                </p>
              </article>
            </div>
          </div>
        </section>

        {/* Connected Architecture */}
        <section className="py-20 bg-[#F4EFE5] border-b border-[#D5CEBF]" id="architecture">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-2xl mx-auto mb-14">
              <span className="text-xs font-tag tracking-wider uppercase text-[#3F6B52] font-semibold mb-2 block">
                System Topology
              </span>
              <h2 className="text-3xl font-bold tracking-tight text-[#121C18] mb-3">
                End-to-End Governance Architecture
              </h2>
              <p className="text-[#4A5550] text-sm font-sans">
                Deterministic processing stages anchored by mandatory underwriter validation.
              </p>
            </div>

            <div className="overflow-x-auto pb-6 pt-2">
              <div className="min-w-[980px] flex items-center justify-between gap-2 px-2">
                <div className="px-4 py-2.5 rounded-full border border-[#D5CEBF] bg-[#EBE5D9] text-xs font-mono font-medium text-[#121C18] whitespace-nowrap">
                  Upload SOV
                </div>
                <div className="w-8 h-[1.5px] bg-[#D5CEBF] mx-1"></div>
                <div className="px-4 py-2.5 rounded-full border border-[#D5CEBF] bg-[#EBE5D9] text-xs font-mono font-medium text-[#121C18] whitespace-nowrap">
                  Sheet Intelligence
                </div>
                <div className="w-8 h-[1.5px] bg-[#D5CEBF] mx-1"></div>
                <div className="px-4 py-2.5 rounded-full border border-[#D5CEBF] bg-[#EBE5D9] text-xs font-mono font-medium text-[#121C18] whitespace-nowrap">
                  Schema Mapping
                </div>
                <div className="w-8 h-[1.5px] bg-[#D5CEBF] mx-1"></div>
                <div className="px-4 py-2.5 rounded-full border border-[#D5CEBF] bg-[#EBE5D9] text-xs font-mono font-medium text-[#121C18] whitespace-nowrap">
                  Data Quality Scan
                </div>
                <div className="w-8 h-[1.5px] bg-[#00C878] mx-1"></div>
                <div className="px-5 py-3 rounded-full bg-[#00C878] text-[#0E3B28] text-xs font-mono font-bold tracking-wide flex items-center gap-2 whitespace-nowrap">
                  <span className="material-symbols-outlined text-[16px]">verified_user</span>
                  Human Review Gate
                </div>
                <div className="w-8 h-[1.5px] bg-[#00C878] mx-1"></div>
                <div className="px-4 py-2.5 rounded-full border border-[#D5CEBF] bg-[#EBE5D9] text-xs font-mono font-medium text-[#121C18] whitespace-nowrap">
                  Transformation Engine
                </div>
                <div className="w-8 h-[1.5px] bg-[#D5CEBF] mx-1"></div>
                <div className="px-4 py-2.5 rounded-full border border-[#D5CEBF] bg-[#EBE5D9] text-xs font-mono font-semibold text-[#0E3B28] whitespace-nowrap">
                  Standardized Output
                </div>
              </div>
            </div>

            <div className="mt-8 text-center">
              <p className="text-xs font-tag text-[#8B9490]">
                Deterministic rule engines guarantee that zero automated modifications enter exposure modeling datasets without authenticated user approval.
              </p>
            </div>
          </div>
        </section>

        {/* Closing CTA */}
        <section className="py-20 bg-[#0E3B28] text-[#F4EFE5]" id="start">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <div className="max-w-3xl mx-auto flex flex-col items-center">
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F4EFE5] mb-4">
                Ready to accelerate your exposure data pipeline?
              </h2>
              <p className="text-base sm:text-lg text-[#D1F2DE] mb-9 font-sans leading-relaxed max-w-2xl">
                Eliminate days of manual spreadsheet clean-up. Standardize schedules in seconds with full underwriter control and audit immutability.
              </p>
              <Link
                className="inline-flex items-center justify-center bg-[#00C878] hover:bg-[#00b56c] text-[#0E3B28] font-bold text-base px-9 py-4 rounded-full mb-10 transition-colors"
                href="/signin"
              >
                Start Analysis
              </Link>
              <div className="pt-6 border-t border-[#1C4E36] w-full flex flex-wrap items-center justify-center gap-y-2 gap-x-6 text-xs text-[#7FE3B0]/80 font-tag">
                <span className="flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[15px] text-[#00C878]">lock</span>
                  AES-256 Encrypted
                </span>
                <span className="text-[#1C4E36]">•</span>
                <span>SOC2 Type II Certified Process</span>
                <span className="text-[#1C4E36]">•</span>
                <span>Never Trains on Proprietary Portfolio Data</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-[#EBE5D9] border-t border-[#D5CEBF] py-12 text-sm text-[#4A5550]" id="governance">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 rounded-full bg-[#0E3B28] flex items-center justify-center text-[#00C878] font-bold text-xs">
                S
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="font-bold text-[#121C18] font-heading">SOVIA</span>
                <span className="text-[#8B9490]">© 2025 SOVIA Intelligence Systems. All rights reserved.</span>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-6 text-xs font-tag">
              <a className="hover:text-[#0E3B28] transition-colors" href="#architecture">
                Security Architecture
              </a>
              <a className="hover:text-[#0E3B28] transition-colors" href="#governance">
                Statutory Compliance
              </a>
              <a className="hover:text-[#0E3B28] transition-colors" href="#features">
                RMS / AIR Bridges
              </a>
              <Link className="hover:text-[#0E3B28] transition-colors" href="/signin">
                Enterprise Sign In
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
