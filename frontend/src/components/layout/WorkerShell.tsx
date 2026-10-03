'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { useWorkflowStore } from '@/store/workflow-store';

interface WorkerShellProps {
  children: React.ReactNode;
}

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/worker/dashboard', icon: 'dashboard' },
  { label: 'Upload SOV', path: '/worker/upload', icon: 'upload_file' },
  { label: 'Analysis', path: '/worker/analysis', icon: 'analytics' },
  { label: 'Mapping Review', path: '/worker/mapping-review', icon: 'schema' },
  { label: 'Data Quality', path: '/worker/data-quality', icon: 'verified' },
  { label: 'Transformation', path: '/worker/transformation', icon: 'transform' },
  { label: 'Output', path: '/worker/output', icon: 'output' },
  { label: 'Audit Log', path: '/worker/audit-log', icon: 'history' },
];

export default function WorkerShell({ children }: WorkerShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const { getActiveSession, sessions, setActiveSessionId } = useWorkflowStore();
  const activeSession = getActiveSession();

  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchFocused, setSearchFocused] = useState(false);

  const menuRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  // Close menus on outside click or Escape
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setSearchFocused(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setUserMenuOpen(false);
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

  const displayName = user?.name || 'A. Sharma';
  const displayAvatar = user?.avatar || 'AS';

  // Filter sessions matching global search query
  const matchingSessions = searchQuery.trim()
    ? sessions.filter(
        (s) =>
          s.fileName.toLowerCase().includes(searchQuery.toLowerCase()) ||
          s.id.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : [];

  return (
    <div className="min-h-screen bg-[#F4EFE5] text-[#121C18]">
      {/* Top Header */}
      <header className="fixed top-0 left-0 right-0 z-50 h-14 bg-[#F4EFE5] border-b border-[#D5CEBF] px-4 sm:px-6 flex items-center justify-between">
        {/* Left: Mobile Toggle + Brand */}
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => setMobileNavOpen(!mobileNavOpen)}
            className="md:hidden p-1.5 rounded-lg text-[#4A5550] hover:bg-[#EBE5D9] hover:text-[#121C18] transition-colors cursor-pointer"
            aria-label="Toggle navigation menu"
          >
            <span className="material-symbols-outlined text-[22px]">
              {mobileNavOpen ? 'close' : 'menu'}
            </span>
          </button>

          <Link href="/worker/dashboard" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-[#0E3B28] flex items-center justify-center text-[#00C878] font-bold text-sm">
              S
            </div>
            <span className="font-heading font-bold text-[20px] tracking-tight text-[#121C18] leading-none">
              SOVIA
            </span>
          </Link>
        </div>

        {/* Center: Search input */}
        <div ref={searchRef} className="relative hidden sm:flex items-center justify-center">
          <div className="relative flex items-center w-72 md:w-96 px-3 py-1.5 rounded-full border border-[#D5CEBF] bg-[#EBE5D9] focus-within:border-[#00C878] focus-within:bg-[#F4EFE5] transition-colors">
            <span className="material-symbols-outlined text-[#8B9490] text-[18px] mr-2">search</span>
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setSearchFocused(true)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && searchQuery.trim()) {
                  router.push(`/worker/dashboard`);
                  setSearchFocused(false);
                }
              }}
              className="w-full bg-transparent border-0 outline-none text-[#121C18] placeholder-[#8B9490] text-[13px] leading-tight"
              placeholder="Search sessions, workbooks... (⌘K)"
              type="text"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="text-[#8B9490] hover:text-[#121C18] p-0.5"
              >
                <span className="material-symbols-outlined text-[14px]">close</span>
              </button>
            )}
          </div>

          {/* Quick search dropdown */}
          {searchFocused && searchQuery.trim().length > 0 && (
            <div className="absolute top-full mt-2 w-full bg-[#F4EFE5] border border-[#D5CEBF] rounded-lg shadow-lg py-2 z-50 max-h-64 overflow-y-auto">
              <div className="px-3 py-1 text-[11px] font-tag text-[#8B9490] uppercase tracking-wider font-semibold">
                Sessions & Workbooks ({matchingSessions.length})
              </div>
              {matchingSessions.length === 0 ? (
                <div className="px-3 py-2 text-xs text-[#8B9490]">No matching sessions found.</div>
              ) : (
                matchingSessions.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => {
                      setActiveSessionId(s.id);
                      setSearchQuery('');
                      setSearchFocused(false);
                      router.push('/worker/dashboard');
                    }}
                    className="w-full px-3 py-2 text-left hover:bg-[#EBE5D9] flex items-center justify-between text-xs cursor-pointer"
                  >
                    <div>
                      <div className="font-heading font-semibold text-[#121C18]">{s.fileName}</div>
                      <div className="text-[10px] text-[#8B9490]">{s.id} · {s.rowCount} rows</div>
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

        {/* Right: User Menu */}
        <div ref={menuRef} className="relative flex items-center">
          <button
            type="button"
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center gap-2 cursor-pointer outline-none py-1 px-1.5 rounded-lg hover:bg-[#EBE5D9] transition-colors"
          >
            <div className="w-8 h-8 rounded-full flex items-center justify-center font-medium text-xs shrink-0 select-none bg-[#D1F2DE] text-[#121C18]">
              {displayAvatar}
            </div>
            <span className="font-heading font-medium text-sm text-[#121C18] whitespace-nowrap hidden sm:inline">
              {displayName}
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full font-medium whitespace-nowrap bg-[#D1F2DE] text-[#0E3B28]">
              Worker
            </span>
            <span className="material-symbols-outlined text-[18px] text-[#8B9490]">expand_more</span>
          </button>

          {userMenuOpen && (
            <div className="absolute right-0 top-full mt-2 w-52 bg-[#F4EFE5] border border-[#D5CEBF] rounded-lg py-1 z-50 shadow-md">
              <div className="px-3 py-2 text-xs text-[#8B9490] border-b border-[#D5CEBF]">
                Signed in as <strong className="text-[#121C18] block">{displayName}</strong>
                <span className="text-[11px] text-[#4A5550]">worker123@ex.com</span>
              </div>
              <Link
                href="/worker/dashboard"
                onClick={() => setUserMenuOpen(false)}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs text-[#121C18] hover:bg-[#EBE5D9] transition-colors"
              >
                <span className="material-symbols-outlined text-[16px] text-[#4A5550]">dashboard</span>
                Dashboard
              </Link>
              <button
                type="button"
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs text-[#8C3B24] hover:bg-[#EBE5D9] transition-colors cursor-pointer text-left border-t border-[#D5CEBF]"
              >
                <span className="material-symbols-outlined text-[16px]">logout</span>
                Sign out
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Mobile Drawer Overlay */}
      {mobileNavOpen && (
        <div
          onClick={() => setMobileNavOpen(false)}
          className="fixed inset-0 z-40 bg-black/30 backdrop-blur-xs md:hidden"
        />
      )}

      {/* Sidebar: Desktop & Mobile Drawer */}
      <aside
        className={`fixed left-0 top-14 h-[calc(100vh-3.5rem)] w-60 bg-[#F4EFE5] border-r border-[#D5CEBF] z-40 flex flex-col justify-between p-4 select-none transition-transform duration-200 ease-in-out ${
          mobileNavOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="flex-1 overflow-y-auto">
          <div className="font-tag text-[11px] text-[#8B9490] uppercase tracking-wider px-3 mb-2 font-semibold">
            Operations
          </div>
          <nav className="flex flex-col gap-1">
            {NAV_ITEMS.map((item) => {
              const isActive =
                pathname === item.path ||
                (item.path !== '/worker/dashboard' && pathname.startsWith(item.path));
              return (
                <Link
                  key={item.path}
                  href={item.path}
                  onClick={() => setMobileNavOpen(false)}
                  className={`flex items-center gap-2.5 px-3 py-2 rounded-lg font-heading text-[13px] transition-colors ${
                    isActive
                      ? 'bg-[#00C878] text-[#0E3B28] font-bold shadow-none'
                      : 'text-[#4A5550] hover:bg-[#EBE5D9] hover:text-[#121C18]'
                  }`}
                >
                  <span
                    className={`material-symbols-outlined text-[18px] ${
                      isActive ? 'text-[#0E3B28]' : 'text-[#8B9490]'
                    }`}
                  >
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Active Session Card */}
        <div className="pt-3 border-t border-[#D5CEBF]">
          <div className="bg-[#EBE5D9] rounded-lg p-3 border border-[#D5CEBF]">
            <div className="font-tag text-[10px] uppercase tracking-wider text-[#8B9490] mb-1 font-semibold">
              Active Session
            </div>
            <div className="font-heading font-semibold text-[12px] text-[#121C18] truncate mb-2">
              {activeSession.fileName}
            </div>
            <div className="flex items-center justify-between">
              <span className="font-tag text-[11px] text-[#8B9490]">Status</span>
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded-full font-tag text-[11px] font-medium capitalize border ${
                  activeSession.status === 'approved'
                    ? 'bg-[#D1F2DE] text-[#0E3B28] border-[#7FE3B0]'
                    : activeSession.status === 'returned'
                    ? 'bg-[#FBEBE8] text-[#8C3B24] border-[#8C3B24]/40'
                    : activeSession.status === 'awaiting'
                    ? 'bg-[#F7ECC8] text-[#B87A1E] border-[#B87A1E]/40'
                    : 'bg-[#D1F2DE] text-[#0E3B28] border-[#7FE3B0]'
                }`}
              >
                {activeSession.status === 'awaiting' ? 'Awaiting Review' : activeSession.status}
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="pl-0 md:pl-60 transition-[padding]">
        <main className="w-full min-h-[calc(100vh-3.5rem)] pt-18 md:pt-16 bg-[#F4EFE5] p-4 sm:p-6 pb-12">
          {children}
        </main>
      </div>
    </div>
  );
}
