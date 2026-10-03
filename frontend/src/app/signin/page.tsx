'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuthStore, WORKER_USER, MANAGER_USER } from '@/store/auth-store';

export default function SignInPage() {
  const router = useRouter();
  const { user, login, logout, setUser } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [demoState, setDemoState] = useState<'default' | 'invalid' | 'google_fail' | 'authenticated'>('default');
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [routingNotice, setRoutingNotice] = useState<string | null>(null);
  const [infoDialog, setInfoDialog] = useState<'privacy' | 'security' | 'help' | null>(null);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setInfoDialog(null);
      }
    };
    if (infoDialog) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [infoDialog]);

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    setIsLoading(true);

    setTimeout(() => {
      setIsLoading(false);
      const res = login(email, password);
      if (res.success && res.user) {
        setRoutingNotice(`Authenticated as ${res.user.name} (${res.user.role}). Redirecting...`);
        setTimeout(() => {
          if (res.user?.role === 'manager') {
            router.push('/manager/overview');
          } else {
            router.push('/worker/dashboard');
          }
        }, 600);
      } else {
        setErrorMessage(res.error || 'Incorrect email or password.');
      }
    }, 400);
  };

  const handleQuickLogin = (role: 'worker' | 'manager') => {
    if (role === 'manager') {
      setEmail(MANAGER_USER.email);
      setPassword('123456');
      setUser(MANAGER_USER);
      setRoutingNotice('Authenticated as S. Reynolds (Manager). Redirecting...');
      setTimeout(() => router.push('/manager/overview'), 500);
    } else {
      setEmail(WORKER_USER.email);
      setPassword('123456');
      setUser(WORKER_USER);
      setRoutingNotice('Authenticated as A. Sharma (Worker). Redirecting...');
      setTimeout(() => router.push('/worker/dashboard'), 500);
    }
  };

  const handleDemoStateChange = (state: 'default' | 'invalid' | 'google_fail' | 'authenticated') => {
    setDemoState(state);
    if (state === 'invalid') {
      setErrorMessage('Incorrect email or password. Please verify your credentials.');
    } else if (state === 'authenticated') {
      setUser(WORKER_USER);
      setErrorMessage('');
    } else {
      setErrorMessage('');
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col md:flex-row overflow-x-hidden bg-[#F4EFE5]">
      {/* LEFT SIDE: BRAND PANEL (50% viewport width) */}
      <aside className="w-full md:w-1/2 bg-[#0E3B28] text-[#F4EFE5] flex flex-col justify-between p-8 sm:p-12 lg:p-16 min-h-[460px] md:min-h-screen border-b md:border-b-0 md:border-r border-[#D5CEBF] relative">
        {/* Top Brand / Logo */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-[#184631] border border-[#20583E] flex items-center justify-center text-[#00C878] font-bold text-base">
            S
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-heading font-bold text-lg tracking-tight text-[#F4EFE5]">
                SOVIA
              </span>
              <span className="font-tag text-[10px] tracking-wider uppercase px-1.5 py-0.5 rounded bg-[#184631] text-[#7FE3B0] border border-[#20583E]">
                ENTERPRISE
              </span>
            </div>
            <span className="font-tag text-[11px] text-[#7FE3B0]/80 tracking-wide">
              Intelligent Data Automation
            </span>
          </div>
        </div>

        {/* Centered Brand Value Proposition */}
        <div className="max-w-md my-auto py-10 md:py-0">
          <h1 className="font-heading text-3xl sm:text-4xl lg:text-[40px] font-bold text-[#F4EFE5] tracking-tight leading-[1.15] mb-5">
            Clean SOV data.
            <br />
            Stay in control.
          </h1>
          <p className="text-[#D1F2DE]/90 text-sm sm:text-base leading-relaxed mb-8 font-sans">
            SOVIA helps transform inconsistent, multi-tab schedule of values into standardized, actuarial-ready output with deterministic precision and cryptographic auditability — keeping humans in control at every gate.
          </p>

          {/* Three Concise Value Points */}
          <div className="space-y-4 pt-2 border-t border-[#1C4E36]">
            <div className="flex items-center gap-3.5">
              <div className="w-6 h-6 rounded-full bg-[#184631] border border-[#2B664A] flex items-center justify-center shrink-0">
                <span className="material-symbols-outlined text-[16px] text-[#7FE3B0]">check</span>
              </div>
              <span className="font-heading text-sm font-medium text-[#F4EFE5]">
                AI-assisted SOV analysis
              </span>
            </div>

            <div className="flex items-center gap-3.5">
              <div className="w-6 h-6 rounded-full bg-[#184631] border border-[#2B664A] flex items-center justify-center shrink-0">
                <span className="material-symbols-outlined text-[16px] text-[#7FE3B0]">check</span>
              </div>
              <span className="font-heading text-sm font-medium text-[#F4EFE5]">
                Human-controlled approvals
              </span>
            </div>

            <div className="flex items-center gap-3.5">
              <div className="w-6 h-6 rounded-full bg-[#184631] border border-[#2B664A] flex items-center justify-center shrink-0">
                <span className="material-symbols-outlined text-[16px] text-[#7FE3B0]">check</span>
              </div>
              <span className="font-heading text-sm font-medium text-[#F4EFE5]">
                Complete transformation history
              </span>
            </div>
          </div>
        </div>

        {/* Bottom Meta Note */}
        <div className="flex items-center justify-between text-xs text-[#7FE3B0]/70 pt-6 border-t border-[#1C4E36]">
          <span className="font-sans">Commercial Risk Underwriting Infrastructure</span>
          <span className="font-tag uppercase tracking-widest text-[10px] text-[#7FE3B0]">
            SOC 2 TYPE II COMPLIANT
          </span>
        </div>
      </aside>

      {/* RIGHT SIDE: SIGN IN FORM (50% viewport width) */}
      <main className="w-full md:w-1/2 bg-[#F4EFE5] flex flex-col justify-between p-6 sm:p-10 lg:p-16 min-h-screen">
        {/* Top Utility / Back to Home link */}
        <div className="flex justify-between items-center w-full">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-heading font-medium text-[#4A5550] hover:text-[#121C18]"
          >
            <span className="material-symbols-outlined text-[16px]">arrow_back</span>
            Back to Home
          </Link>

          {/* Quick Demo State Switcher */}
          <div className="flex items-center gap-1.5 bg-[#EBE5D9] border border-[#D5CEBF] px-2.5 py-1 rounded-full text-[11px] font-sans text-[#4A5550]">
            <span className="text-[#8B9490]">Demo State:</span>
            <select
              value={demoState}
              onChange={(e) => handleDemoStateChange(e.target.value as 'default' | 'invalid' | 'google_fail' | 'authenticated')}
              className="bg-transparent font-medium text-[#121C18] focus:outline-none cursor-pointer"
            >
              <option value="default">Default State</option>
              <option value="invalid">Invalid Credentials</option>
              <option value="google_fail">Google Auth Failure</option>
              <option value="authenticated">Already Authenticated</option>
            </select>
          </div>
        </div>

        {/* Centered Form Container (Max-width 400px) */}
        <div className="w-full max-w-[400px] mx-auto my-auto py-8">
          <div className="mb-6">
            <h2 className="font-heading text-2xl sm:text-[26px] font-bold text-[#121C18] tracking-tight mb-1.5">
              Sign in to SOVIA
            </h2>
            <p className="font-sans text-sm text-[#4A5550]">
              Access your SOV workspace and transformation history.
            </p>
          </div>

          {/* INLINE ALERT: Invalid Credentials (Amber state) */}
          {(errorMessage || demoState === 'invalid') && (
            <div className="mb-5 p-3 rounded-md bg-[#F7ECC8] border border-[#B87A1E] text-xs font-sans text-[#B87A1E] flex items-start gap-2.5">
              <span className="material-symbols-outlined text-[#B87A1E] text-[18px] shrink-0 mt-0.5">
                warning
              </span>
              <div>
                <span className="font-semibold block font-heading">Incorrect email or password.</span>
                <span>Please verify your credentials or select a quick demo role below.</span>
              </div>
            </div>
          )}

          {/* INLINE ALERT: Google Auth Failure */}
          {demoState === 'google_fail' && (
            <div className="mb-5 p-3 rounded-md bg-[#F7ECC8] border border-[#B87A1E] text-xs font-sans text-[#B87A1E] flex items-center gap-2.5">
              <span className="material-symbols-outlined text-[#B87A1E] text-[18px] shrink-0">
                error
              </span>
              <span>Google sign-in could not be completed. Please use prototype credentials.</span>
            </div>
          )}

          {/* INLINE BANNER: Already Authenticated */}
          {(user || demoState === 'authenticated') && (
            <div className="mb-6 p-4 rounded-md bg-[#EBE5D9] border border-[#D5CEBF] text-xs font-sans text-[#121C18]">
              <div className="flex items-center gap-2 mb-2 font-heading font-semibold text-sm text-[#0E3B28]">
                <span className="w-2 h-2 rounded-full bg-[#00C878]"></span>
                Active Session Detected
              </div>
              <p className="text-[#4A5550] mb-3">
                You are currently signed in as{' '}
                <strong className="text-[#121C18]">
                  {user?.name || 'A. Sharma'} ({user?.role === 'manager' ? 'Manager' : 'Worker'})
                </strong>
                .
              </p>
              <div className="flex gap-2">
                <Link
                  href={user?.role === 'manager' ? '/manager/overview' : '/worker/dashboard'}
                  className="flex-1 text-center py-2 px-3 rounded-full bg-[#00C878] text-[#0E3B28] font-heading font-semibold text-xs hover:bg-[#00b56c]"
                >
                  Go to Workspace →
                </Link>
                <button
                  type="button"
                  onClick={() => {
                    logout();
                    setDemoState('default');
                  }}
                  className="py-2 px-3 rounded-full border border-[#D5CEBF] bg-[#F4EFE5] text-[#4A5550] font-heading text-xs hover:text-[#121C18] cursor-pointer"
                >
                  Sign Out
                </button>
              </div>
            </div>
          )}

          {/* FORM */}
          <form onSubmit={handleFormSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block font-sans text-xs font-semibold text-[#121C18] mb-1.5">
                Email
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Work email (e.g. worker123@ex.com or manager123@ex.com)"
                required
                className="w-full bg-[#F4EFE5] border border-[#D5CEBF] rounded-lg px-3.5 py-2.5 text-sm text-[#121C18] placeholder-[#8B9490] focus:outline-none focus:border-[#00C878]"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label htmlFor="password" className="block font-sans text-xs font-semibold text-[#121C18]">
                  Password
                </label>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password (123456)"
                  required
                  className="w-full bg-[#F4EFE5] border border-[#D5CEBF] rounded-lg px-3.5 py-2.5 pr-10 text-sm text-[#121C18] placeholder-[#8B9490] focus:outline-none focus:border-[#00C878]"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#8B9490] hover:text-[#121C18] p-1 cursor-pointer"
                  aria-label="Toggle password visibility"
                >
                  <span className="material-symbols-outlined text-[18px]">
                    {showPassword ? 'visibility_off' : 'visibility'}
                  </span>
                </button>
              </div>
            </div>

            {/* Primary Action Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 px-5 rounded-full bg-[#00C878] hover:bg-[#00b56c] text-[#0E3B28] font-heading font-semibold text-sm flex items-center justify-center gap-2 border border-transparent disabled:opacity-60 cursor-pointer transition-colors"
              >
                <span>{isLoading ? 'Signing in...' : 'Sign In'}</span>
                {!isLoading && (
                  <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                )}
              </button>
            </div>

            {/* Divider */}
            <div className="relative my-5">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-[#D5CEBF]"></div>
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-[#F4EFE5] px-3 font-tag uppercase text-[#8B9490] tracking-wider">
                  QUICK PROTOTYPE ACCESS
                </span>
              </div>
            </div>

            {/* Quick Prototype Login Buttons */}
            <div className="grid grid-cols-2 gap-2.5">
              <button
                type="button"
                onClick={() => handleQuickLogin('worker')}
                className="py-2.5 px-3 rounded-lg border border-[#D5CEBF] bg-[#EBE5D9] hover:bg-[#E5DEC9] text-[#121C18] text-xs font-heading font-semibold flex flex-col items-center justify-center text-center cursor-pointer transition-colors"
              >
                <span className="text-[#0E3B28] font-bold">Worker Demo</span>
                <span className="text-[10px] text-[#4A5550]">A. Sharma (Ops)</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('manager')}
                className="py-2.5 px-3 rounded-lg border border-[#D5CEBF] bg-[#EBE5D9] hover:bg-[#E5DEC9] text-[#121C18] text-xs font-heading font-semibold flex flex-col items-center justify-center text-center cursor-pointer transition-colors"
              >
                <span className="text-[#0E3B28] font-bold">Manager Demo</span>
                <span className="text-[10px] text-[#4A5550]">S. Reynolds (Risk Lead)</span>
              </button>
            </div>
          </form>

          {/* Feedback Notice */}
          {routingNotice && (
            <div className="mt-5 p-3 rounded-lg bg-[#D1F2DE] border border-[#7FE3B0] text-center text-xs font-heading text-[#0E3B28] font-semibold flex items-center justify-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#00C878] animate-ping"></span>
              <span>{routingNotice}</span>
            </div>
          )}
        </div>

        {/* Bottom Footer */}
        <div className="w-full max-w-[400px] mx-auto pt-6 border-t border-[#DFD9CC] flex items-center justify-between text-[11px] text-[#8B9490]">
          <span className="font-sans">© 2025 SOVIA Intelligence Inc.</span>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setInfoDialog('privacy')}
              className="hover:text-[#4A5550] cursor-pointer"
            >
              Privacy
            </button>
            <span className="text-[#D5CEBF]">·</span>
            <button
              type="button"
              onClick={() => setInfoDialog('security')}
              className="hover:text-[#4A5550] cursor-pointer"
            >
              Security
            </button>
            <span className="text-[#D5CEBF]">·</span>
            <button
              type="button"
              onClick={() => setInfoDialog('help')}
              className="hover:text-[#4A5550] cursor-pointer"
            >
              Help
            </button>
          </div>
        </div>

        {/* Informational Policy Modal */}
        {infoDialog && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
            onClick={() => setInfoDialog(null)}
          >
            <div
              className="w-full max-w-md bg-[#F4EFE5] border border-[#D5CEBF] rounded-xl p-5 shadow-lg text-[#121C18]"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between pb-3 border-b border-[#D5CEBF]">
                <h3 className="font-heading font-bold text-sm text-[#121C18]">
                  {infoDialog === 'privacy' && 'Enterprise Privacy Policy'}
                  {infoDialog === 'security' && 'Security & Data Governance'}
                  {infoDialog === 'help' && 'SOVIA Support & Helpdesk'}
                </h3>
                <button
                  type="button"
                  onClick={() => setInfoDialog(null)}
                  className="text-[#8B9490] hover:text-[#121C18] cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[18px]">close</span>
                </button>
              </div>

              <div className="py-4 text-xs font-sans text-[#4A5550] leading-relaxed space-y-2">
                {infoDialog === 'privacy' && (
                  <>
                    <p>
                      SOVIA adheres to strict zero-training isolation standards. Proprietary portfolio data, broker schedules of values, and location coordinates are never used to train generalized LLMs or shared across tenants.
                    </p>
                    <p>
                      All transformation checkpoints are pinned with cryptographic SHA-256 signatures for immutable underwriter provenance.
                    </p>
                  </>
                )}
                {infoDialog === 'security' && (
                  <>
                    <p>
                      Enterprise security controls are built to SOC 2 Type II and ISO 27001 standards:
                    </p>
                    <ul className="list-disc pl-4 space-y-1">
                      <li>AES-256 GCM encryption at rest with tenant-isolated customer managed keys (CMK).</li>
                      <li>TLS 1.3 in-transit encryption with certificate pinning.</li>
                      <li>Role-Based Access Control (RBAC) enforcing dual-authorization maker-checker L4 rules.</li>
                    </ul>
                  </>
                )}
                {infoDialog === 'help' && (
                  <>
                    <p>
                      For technical support, custom RMS/AIR integration profiles, or underwriter role provisioning:
                    </p>
                    <div className="p-3 bg-[#EBE5D9] rounded border border-[#D5CEBF] font-mono text-[11px] text-[#121C18] space-y-1">
                      <div>Enterprise Support: support@sovia-risk.com</div>
                      <div>Emergency Operations: +1 (800) 555-SOVI (24/7 SLA)</div>
                      <div>Demo Access: Quick sign-in buttons available on this screen</div>
                    </div>
                  </>
                )}
              </div>

              <div className="flex justify-end pt-3 border-t border-[#D5CEBF]">
                <button
                  type="button"
                  onClick={() => setInfoDialog(null)}
                  className="px-4 py-1.5 rounded-lg bg-[#00C878] text-[#0E3B28] text-xs font-heading font-bold hover:bg-[#00b56c] cursor-pointer"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
