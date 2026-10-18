"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { get } from "@/lib/api";
import { Search, Building2, MapPin, GraduationCap } from "lucide-react";

interface College {
  id: string;
  college_code: string;
  name: string;
  college_type: string | null;
  state: string | null;
  district: string | null;
  naac_grade: string | null;
  established_year: number | null;
  source: string;
  verification_status: string;
}

interface CollegesResponse {
  items: College[];
  total: number;
  page: number;
  page_size: number;
}

export default function AdminCollegesPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery<CollegesResponse>({
    queryKey: ["admin-colleges", page, search],
    queryFn: () =>
      get(`/admin/colleges?page=${page}&page_size=20${search ? `&search=${encodeURIComponent(search)}` : ""}`),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">Colleges</h1>
          <p className="text-muted-foreground mt-1">
            {data?.total ?? 0} colleges in the database
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="search"
          placeholder="Search colleges…"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="w-full rounded-lg border bg-background pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          aria-label="Search colleges"
        />
      </div>

      {/* Table */}
      <div className="rounded-xl border bg-card overflow-x-auto">
        {isLoading ? (
          <div className="py-16 text-center text-muted-foreground">Loading…</div>
        ) : !data?.items.length ? (
          <div className="py-16 text-center text-muted-foreground">
            <Building2 className="mx-auto h-12 w-12 mb-3 opacity-30" />
            <p className="font-medium">No colleges found</p>
            <p className="text-sm mt-1">Import college data from the Data Import section.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50">
              <tr>
                <th className="px-5 py-3 text-left font-medium">Name</th>
                <th className="px-5 py-3 text-left font-medium">Code</th>
                <th className="px-5 py-3 text-left font-medium">Type</th>
                <th className="px-5 py-3 text-left font-medium">Location</th>
                <th className="px-5 py-3 text-left font-medium">NAAC</th>
                <th className="px-5 py-3 text-left font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.items.map((c) => (
                <tr key={c.id} className="hover:bg-muted/30">
                  <td className="px-5 py-3">
                    <p className="font-medium">{c.name}</p>
                    <p className="text-xs text-muted-foreground">{c.source}</p>
                  </td>
                  <td className="px-5 py-3 font-mono text-xs">{c.college_code}</td>
                  <td className="px-5 py-3 capitalize">{c.college_type ?? "—"}</td>
                  <td className="px-5 py-3">
                    <span className="flex items-center gap-1 text-muted-foreground">
                      <MapPin className="h-3 w-3" />
                      {[c.district, c.state].filter(Boolean).join(", ") || "—"}
                    </span>
                  </td>
                  <td className="px-5 py-3">{c.naac_grade ?? "—"}</td>
                  <td className="px-5 py-3">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      c.verification_status === "verified"
                        ? "bg-green-100 text-green-700"
                        : "bg-yellow-100 text-yellow-700"
                    }`}>
                      {c.verification_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {data && data.total > 20 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Page {page} of {Math.ceil(data.total / 20)}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="rounded-md border px-3 py-1.5 text-sm disabled:opacity-50 hover:bg-accent"
            >Previous</button>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={page >= Math.ceil(data.total / 20)}
              className="rounded-md border px-3 py-1.5 text-sm disabled:opacity-50 hover:bg-accent"
            >Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
