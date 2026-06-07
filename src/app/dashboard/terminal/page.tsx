import { Topbar } from '@/components/dashboard/Topbar';
import { KuzoTerminal } from '@/components/dashboard/KuzoTerminal';

export const dynamic = 'force-dynamic';

export default function TerminalPage() {
  return (
    <>
      <Topbar pageTitle="KUZO Pro Terminal · Chain Ops" />
      <main className="flex-1 px-4 py-4 sm:px-6 sm:py-6">
        <KuzoTerminal />
      </main>
    </>
  );
}
