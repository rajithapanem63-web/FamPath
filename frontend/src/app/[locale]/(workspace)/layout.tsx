"use client";

import { useEffect, useState } from "react";
import { useRouter, Link, usePathname } from "@/i18n/routing";
import { useAuthStore } from "@/stores/authStore";
import { useTranslations } from "next-intl";
import {
  Home, Brain, Star, BarChart2, Heart, DollarSign,
  MessageCircle, List, Clock, LogOut, Menu, X, User,
  ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard",    icon: Home,           key: "dashboard" },
  { href: "/predict",      icon: BarChart2,       key: "predict" },
  { href: "/aptitude",     icon: Brain,           key: "aptitude" },
  { href: "/alignment",    icon: Heart,           key: "alignment" },
  { href: "/preferences",  icon: Star,            key: "preferences" },
  { href: "/cost",         icon: DollarSign,      key: "cost" },
  { href: "/chatbot",      icon: MessageCircle,   key: "chatbot" },
  { href: "/shortlist",    icon: List,            key: "shortlist" },
  { href: "/timeline",     icon: Clock,           key: "timeline" },
];

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, clear } = useAuthStore();
  const t = useTranslations("nav");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => { setHydrated(true); }, []);

  useEffect(() => {
    if (!hydrated) return;
    if (!user) {
      router.replace("/sign-in");
    }
  }, [hydrated, user, router]);

  if (!hydrated || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Loading FamPath…</p>
        </div>
      </div>
    );
  }

  function handleSignOut() {
    clear();
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("access_token");
    }
    router.replace("/sign-in");
  }

  const NavLink = ({ item }: { item: typeof navItems[0] }) => {
    const Icon = item.icon;
    const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
    return (
      <Link
        href={item.href as any}
        onClick={() => setSidebarOpen(false)}
        className={cn(
          "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
          isActive
            ? "bg-primary text-primary-foreground"
            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
        )}
        aria-current={isActive ? "page" : undefined}
      >
        <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
        {t(item.key)}
      </Link>
    );
  };

  const SidebarContent = () => (
    <div className="flex h-full flex-col">
      {/* Logo */}
      <div className="flex items-center gap-2 border-b px-4 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-sm">
          FP
        </div>
        <span className="font-semibold text-lg">FamPath</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1" aria-label="Main navigation">
        <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded focus:bg-background focus:p-2 focus:text-sm">
          Skip to main content
        </a>
        {navItems.map((item) => (
          <NavLink key={item.href} item={item} />
        ))}
      </nav>

      {/* User + sign out */}
      <div className="border-t px-3 py-4 space-y-2">
        <div className="flex items-center gap-2 rounded-lg px-3 py-2 bg-muted">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/20 text-primary text-xs font-bold">
            {(user.full_name || user.email).charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{user.full_name || user.email}</p>
            <p className="truncate text-xs text-muted-foreground capitalize">{user.role}</p>
          </div>
        </div>
        <button
          onClick={handleSignOut}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
          aria-label={t("signOut")}
        >
          <LogOut className="h-4 w-4 shrink-0" aria-hidden="true" />
          {t("signOut")}
        </button>
      </div>
    </div>
  );

  return (
    <div className="flex min-h-screen bg-background">
      {/* Desktop sidebar */}
      <aside className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col border-r bg-card">
        <SidebarContent />
      </aside>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile sidebar panel */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 flex-col border-r bg-card transition-transform duration-200 lg:hidden",
          sidebarOpen ? "flex translate-x-0" : "flex -translate-x-full"
        )}
        aria-label="Mobile navigation"
      >
        <div className="flex items-center justify-between border-b px-4 py-4">
          <span className="font-semibold text-lg">FamPath</span>
          <button
            onClick={() => setSidebarOpen(false)}
            className="rounded-md p-1 hover:bg-accent"
            aria-label="Close navigation"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {navItems.map((item) => (
            <NavLink key={item.href} item={item} />
          ))}
        </div>
        <div className="border-t px-3 py-4">
          <button
            onClick={handleSignOut}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
          >
            <LogOut className="h-4 w-4" />
            {t("signOut")}
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col lg:pl-64">
        {/* Mobile topbar */}
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b bg-card px-4 py-3 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-md p-1.5 hover:bg-accent"
            aria-label="Open navigation"
          >
            <Menu className="h-5 w-5" />
          </button>
          <span className="font-semibold">FamPath</span>
        </header>

        {/* Page content */}
        <main id="main-content" className="flex-1 p-4 md:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
