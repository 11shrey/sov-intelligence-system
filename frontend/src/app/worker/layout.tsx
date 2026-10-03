import RoleGate from '@/components/auth/RoleGate';

export default function WorkerLayout({ children }: { children: React.ReactNode }) {
  return <RoleGate role="worker">{children}</RoleGate>;
}
