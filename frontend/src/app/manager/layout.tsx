import RoleGate from '@/components/auth/RoleGate';

export default function ManagerLayout({ children }: { children: React.ReactNode }) {
  return <RoleGate role="manager">{children}</RoleGate>;
}
