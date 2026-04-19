"use client";

import { usePathname, useRouter } from "next/navigation";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

const AUTH_PATHS = ["/login", "/signup"];

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuth = AUTH_PATHS.includes(pathname);

  if (isAuth) {
    // Auth pages get no sidebar/topbar
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background font-sans text-foreground">
      <Sidebar className="w-64 flex-shrink-0" />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-auto p-6 bg-background">{children}</main>
      </div>
    </div>
  );
}
