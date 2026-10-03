'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { useWorkflowStore } from '@/store/workflow-store';

interface ManagerShellProps {
  children: React.ReactNode;
}

export default function ManagerShell({ children }: ManagerShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const { sessions, setActiveSessionId } = useWorkflowStore();

  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchFocused, setSearchFocused] = useState(false);

  const menuRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click or Escape
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setProfileDropdownOpen(false);
      }
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setSearchFocused(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setProfileDropdownOpen(false);
        setMobileNavOpen(false);
        setSearchFocused(false);
      }
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        const input = searchRef.current?.querySelector('input');
        input?.focus();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  // Close mobile nav on route change
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMobileNavOpen(false);
  }, [pathname]);

  const handleLogout = () => {
    logout();
    router.push('/signin');
  };

  const pendingCount = sessions.filter((s) => s.status === 'awaiting' || s.status === 'ready').length;

  const displayName = user?.name || 'S. Reynolds';
  const displayAvatar = user?.avatar || 'SR';

  const matchingSessions = searchQuery.trim()
    ? sessions.filter(
        (s) =>
          s.fileName.toLowerCase().includes(searchQuery.toLowerCase()) ||
          s.workerName.toLowerCase().includes(searchQuery.toLowerCase()) ||
          s.id.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : [];

  return (
    <div className="min-h-screen flex flex-col bg-[#F4EFE5] text-[#121C18]">
      {/* Top Header: Manager Authenticated Shell */}
      <header className="h-14 border-b border-[#D5CEBF] bg-[#EBE5D9] px-4 sm:px-6 flex items-center justify-between sticky top-0 z-50 select-none">
        {/* Left: Mobile menu toggle + Logo & Institutional Tagline */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          <button
            type="button"
            onClick={() => setMobileNavOpen(!mobileNavOpen)}
            className="md:hidden p-1.5 rounded-lg text-[#4A5550] hover:bg-[#E5DEC9] hover:text-[#121C18] transition-colors cursor-pointer"
            aria-label="Toggle navigation drawer"
          >
            <span className="material-symbols-outlined text-[22px]">
              {mobileNavOpen ? 'close' : 'menu'}
            </span>
          </button>

          <Link href="/manager/overview" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-[#0E3B28] flex items-center justify-center text-[#00C878] font-bold text-sm">
              S
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-heading font-bold text-lg tracking-tight text-[#121C18]">SOVIA</span>
              <span className="font-tag text-[11px] uppercase tracking-wider text-[#8B9490] hidden lg:inline">
                Intelligent Data Automation
              </span>
            </div>
          </Link>
          <span className="text-[#D5CEBF] text-xs hidden sm:inline">|</span>
          <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#E5DEC9] border border-[#D5CEBF]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#00C878]"></span>
            <span className="font-tag text-[10px] font-semibold uppercase tracking-wider text-[#0E3B28]">
              Enterprise Risk Console
            </span>
          </div>
        </div>

        {/* Center: Global Search Bar */}
        <div ref={searchRef} className="relative flex-1 max-w-md mx-4 sm:mx-8 hidden sm:block">
          <div className="relative flex items-center">
            <span className="material-symbols-outlined text-[#8B9490] absolute left-3 pointer-events-none text-[18px]">
              search
            </span>
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setSearchFocused(true)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && searchQuery.trim()) {
                  router.push(`/manager/queue`);
                  setSearchFocused(false);
                }
              }}
              className="w-full bg-[#F4EFE5] border border-[#D5CEBF] rounded-full pl-9 pr-12 py-1.5 text-xs text-[#121C18] placeholder-[#8B9490] focus:outline-none focus:border-[#0E3B28]"
              placeholder="Search portfolio, exceptions, files, workers... (⌘K)"
              type="text"
            />
            <div className="absolute right-3 flex items-center gap-1">
              <span className="font-tag text-[10px] text-[#8B9490] bg-[#EBE5D9] px-1.5 py-0.5 rounded border border-[#D5CEBF]">
                ⌘K
              </span>
            </div>
          </div>

          {/* Quick search dropdown */}
          {searchFocused && searchQuery.trim().length > 0 && (
            <div className="absolute top-full mt-2 w-full bg-[#F4EFE5] border border-[#D5CEBF] rounded-lg shadow-lg py-2 z-50 max-h-64 overflow-y-auto">
              <div className="px-3 py-1 text-[11px] font-tag text-[#8B9490] uppercase tracking-wider font-semibold">
                Portfolios & Workers ({matchingSessions.length})
              </div>
              {matchingSessions.length === 0 ? (
                <div className="px-3 py-2 text-xs text-[#8B9490]">No matching entries found.</div>
              ) : (
                matchingSessions.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => {
                      setActiveSessionId(s.id);
                      setSearchQuery('');
                      setSearchFocused(false);
                      router.push(`/manager/review?id=${s.id}`);
                    }}
                    className="w-full px-3 py-2 text-left hover:bg-[#EBE5D9] flex items-center justify-between text-xs cursor-pointer"
                  >
                    <div>
                      <div className="font-heading font-semibold text-[#121C18]">{s.fileName}</div>
                      <div className="text-[10px] text-[#8B9490]">
                        {s.id} · Submitter: {s.workerName}
                      </div>
                    </div>
                    <span className="text-[10px] uppercase font-tag px-1.5 py-0.5 rounded bg-[#E5DEC9] text-[#4A5550]">
                      {s.status}
                    </span>
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        {/* Right: Manager Identity with Dropdown */}
        <div ref={menuRef} className="flex items-center gap-3">
          <div className="relative">
            <button
              type="button"
              onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
              className="flex items-center gap-2 p-1.5 rounded-lg border border-[#D5CEBF] bg-[#F4EFE5] hover:bg-[#EBE5D9] transition-colors focus:outline-none cursor-pointer"
            >
              <div className="w-7 h-7 rounded-full bg-[#0E3B28] text-[#F4EFE5] font-heading font-semibold text-xs flex items-center justify-center">
                {displayAvatar}
              </div>
              <div className="flex flex-col text-left leading-tight hidden md:block">
                <span className="text-xs font-semibold font-heading text-[#121C18]">{displayName}</span>
                <span className="text-[10px] text-[#8B9490]">Risk Underwriting</span>
              </div>
              <span className="px-2 py-0.5 rounded text-[11px] font-medium font-heading bg-[#0E3B28] text-[#F4EFE5]">
                Manager
              </span>
              <span className="material-symbols-outlined text-[#8B9490] text-[16px]">expand_more</span>
            </button>

            {profileDropdownOpen && (
              <div className="absolute right-0 mt-1 w-52 bg-[#F4EFE5] border border-[#D5CEBF] rounded-md py-1 z-50 shadow-md">
                <div className="px-3 py-2 border-b border-[#D5CEBF]">
                  <p className="text-xs font-medium text-[#121C18]">{displayName}</p>
                  <p className="text-[10px] text-[#8B9490]">manager123@ex.com (Gov & Audit)</p>
                </div>
                <Link
                  href="/manager/overview"
                  onClick={() => setProfileDropdownOpen(false)}
                  className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#121C18] hover:bg-[#EBE5D9] transition-colors"
                >
                  <span className="material-symbols-outlined text-[16px] text-[#4A5550]">group</span>
                  Team Overview
                </Link>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#8C3B24] hover:bg-[#EBE5D9] text-left cursor-pointer border-t border-[#D5CEBF]"
                >
                  <span className="material-symbols-outlined text-[16px]">logout</span>
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Mobile Drawer Overlay */}
      {mobileNavOpen && (
        <div
          onClick={() => setMobileNavOpen(false)}
          className="fixed inset-0 z-40 bg-black/30 backdrop-blur-xs md:hidden"
        />
      )}

      {/* Body Container: Sidebar + Main */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Sidebar: Desktop & Mobile Drawer */}
        <aside
          className={`fixed md:static left-0 top-14 bottom-0 z-40 w-60 bg-[#EBE5D9] border-r border-[#D5CEBF] flex flex-col justify-between select-none flex-shrink-0 min-h-[calc(100vh-3.5rem)] transition-transform duration-200 ease-in-out ${
            mobileNavOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
          }`}
        >
          <div className="p-3">
            <div className="px-3 py-2 text-[10px] font-tag font-semibold tracking-wider text-[#8B9490] uppercase">
              Manager Scope
            </div>
            <nav className="space-y-1">
              {/* Team Overview */}
              <Link
                href="/manager/overview"
                onClick={() => setMobileNavOpen(false)}
                className={`flex items-center gap-2.5 px-3 py-2 rounded text-xs transition-colors ${
                  pathname === '/manager/overview'
                    ? 'font-semibold text-[#0E3B28] bg-[#00C878] border border-[#00C878]'
                    : 'font-medium text-[#4A5550] hover:bg-[#E5DEC9] hover:text-[#121C18]'
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">group</span>
                <span>Team Overview</span>
              </Link>

              {/* Approval Queue */}
              <Link
                href="/manager/queue"
                onClick={() => setMobileNavOpen(false)}
                className={`flex items-center justify-between px-3 py-2 rounded text-xs transition-colors ${
                  pathname === '/manager/queue' || pathname.startsWith('/manager/review')
                    ? 'font-semibold text-[#0E3B28] bg-[#00C878] border border-[#00C878]'
                    : 'font-medium text-[#4A5550] hover:bg-[#E5DEC9] hover:text-[#121C18]'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <span className="material-symbols-outlined text-[18px]">checklist</span>
                  <span>Approval Queue</span>
                </div>
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                    pathname === '/manager/queue'
                      ? 'bg-[#0E3B28] text-[#F4EFE5]'
                      : 'bg-[#E5DEC9] text-[#4A5550]'
                  }`}
                >
                  {pendingCount}
                </span>
              </Link>

              {/* Team */}
              <Link
                href="/manager/team"
                onClick={() => setMobileNavOpen(false)}
                className={`flex items-center gap-2.5 px-3 py-2 rounded text-xs transition-colors ${
                  pathname === '/manager/team'
                    ? 'font-semibold text-[#0E3B28] bg-[#00C878] border border-[#00C878]'
                    : 'font-medium text-[#4A5550] hover:bg-[#E5DEC9] hover:text-[#121C18]'
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">badge</span>
                <span>Team</span>
              </Link>

              {/* Org Audit Log */}
              <Link
                href="/manager/audit-log"
                onClick={() => setMobileNavOpen(false)}
                className={`flex items-center gap-2.5 px-3 py-2 rounded text-xs transition-colors ${
                  pathname === '/manager/audit-log'
                    ? 'font-semibold text-[#0E3B28] bg-[#00C878] border border-[#00C878]'
                    : 'font-medium text-[#4A5550] hover:bg-[#E5DEC9] hover:text-[#121C18]'
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">history_edu</span>
                <span>Org Audit Log</span>
              </Link>
            </nav>
          </div>

          {/* Sidebar Footer: Governance Scope Metadata */}
          <div className="p-3 border-t border-[#D5CEBF] bg-[#EBE5D9]">
            <div className="p-2.5 rounded border border-[#D5CEBF] bg-[#F4EFE5] space-y-1.5">
              <div className="flex items-center justify-between text-[10px] font-tag uppercase tracking-wider text-[#8B9490]">
                <span>Governance Gate</span>
                <span className="text-[#0E3B28] font-bold">L4 Authorize</span>
              </div>
              <div className="text-[11px] font-heading font-medium text-[#121C18]">
                {displayName}
              </div>
              <div className="text-[10px] text-[#4A5550] truncate">
                manager123@ex.com
              </div>
              <div className="pt-1 border-t border-[#DFD9CC] flex items-center justify-between text-[9px] text-[#8B9490]">
                <span>Scope: Enterprise</span>
                <span className="flex items-center gap-1 text-[#0E3B28]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#00C878]"></span>
                  Live Sync
                </span>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 w-full">
          {children}
        </main>
      </div>
    </div>
  );
}
