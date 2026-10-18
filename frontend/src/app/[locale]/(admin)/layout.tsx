"use client";

import { useEffect, useState } from "react";
import { useRouter, Link, usePathname } from "@/i18n/routing";
import { useAuthStore } from "@/stores/authStore";
import { useTranslations } from "next-intl";
import { Database, Upload, BarChart2, LogOut, Menu, X, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

const adminNavItems = [
  { href: "/admin", icon: BarChart2, label: "Dashboard" },
  { href: "/admin/colleges", icon: Database, label: "Colleges" },
  { href: "/admin/import", icon: Upload, label: "Data Import" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, clear } = useAuthStore();
  const [hydrated, setHydrated] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => { setHydrated(true); }, []);

  useEffect(() => {
    if (!hydrated) return;
    if (!user) { router.replace("/sign-in"); return; }
    if (user.role !== "admin") { router.replace("/dashboard"); }
  }, [hydrated, user, router]);

  if (!hydrated || !user || user.role !== "admin") {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  function handleSignOut() {
    clear();
    if (typeof window !== "undefined") sessionStorage.removeItem("access_token");
    router.replace("/sign-in");
  }

  return (
    <div className="flex min-h-screen bg-background">
      {/* Desktop sidebar */}
      <aside className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-56 lg:flex-col border-r bg-card">
        <div className="flex items-center gap-2 border-b px-4 py-4">
          <ShieldCheck className="h-6 w-6 text-primary" />
          <span className="font-semibold">FamPath Admin</span>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {adminNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href as any}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent"
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t px-3 py-4">
          <button onClick={handleSignOut} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-destructive/10 hover:text-destructive">
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex flex-1 flex-col lg:pl-56">
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b bg-card px-4 py-3 lg:hidden">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="rounded-md p-1.5 hover:bg-accent">
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <span className="font-semibold">FamPath Admin</span>
        </header>
        <main className="flex-1 p-4 md:p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
