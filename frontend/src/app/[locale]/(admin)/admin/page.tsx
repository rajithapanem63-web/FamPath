"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { get } from "@/lib/api";
import { BarChart2, Database, TrendingUp, AlertCircle, CheckCircle, Clock, Upload } from "lucide-react";

interface FreshnessRecord {
  dataset_type: string;
  latest_import: string | null;
  record_count: number;
  source: string;
  status: string;
}

export default function AdminDashboard() {
  const { data: freshness, isLoading } = useQuery<FreshnessRecord[]>({
    queryKey: ["admin-freshness"],
    queryFn: () => get("/admin/freshness").then((r: any) => r.records ?? []),
    retry: false,
  });

  const statusIcon = (status: string) => {
    if (status === "fresh") return <CheckCircle className="h-4 w-4 text-green-500" />;
    if (status === "stale") return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    return <Clock className="h-4 w-4 text-muted-foreground" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
        <p className="text-muted-foreground mt-1">Monitor data freshness, imports, and platform health.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border bg-card p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-blue-100 p-2"><Database className="h-5 w-5 text-blue-600" /></div>
            <div>
              <p className="text-sm text-muted-foreground">Datasets</p>
              <p className="text-2xl font-bold">{freshness?.length ?? "—"}</p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border bg-card p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-green-100 p-2"><CheckCircle className="h-5 w-5 text-green-600" /></div>
            <div>
              <p className="text-sm text-muted-foreground">Fresh</p>
              <p className="text-2xl font-bold">{freshness?.filter(f => f.status === "fresh").length ?? "—"}</p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border bg-card p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-yellow-100 p-2"><AlertCircle className="h-5 w-5 text-yellow-600" /></div>
            <div>
              <p className="text-sm text-muted-foreground">Stale / Missing</p>
              <p className="text-2xl font-bold">{freshness?.filter(f => f.status !== "fresh").length ?? "—"}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Data freshness table */}
      <div className="rounded-xl border bg-card">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h2 className="font-semibold">Data Freshness</h2>
        </div>
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="py-12 text-center text-muted-foreground">Loading…</div>
          ) : !freshness?.length ? (
            <div className="py-12 text-center text-muted-foreground">
              <Database className="mx-auto h-10 w-10 mb-3 opacity-30" />
              <p>No data imported yet.</p>
              <p className="text-sm mt-1">Use the Data Import section to upload college, cutoff, and fee data.</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/50">
                <tr>
                  <th className="px-5 py-3 text-left font-medium">Dataset</th>
                  <th className="px-5 py-3 text-left font-medium">Records</th>
                  <th className="px-5 py-3 text-left font-medium">Last Import</th>
                  <th className="px-5 py-3 text-left font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {freshness.map((row) => (
                  <tr key={row.dataset_type} className="hover:bg-muted/30">
                    <td className="px-5 py-3 font-medium capitalize">{row.dataset_type}</td>
                    <td className="px-5 py-3">{row.record_count.toLocaleString("en-IN")}</td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {row.latest_import ? new Date(row.latest_import).toLocaleDateString("en-IN") : "Never"}
                    </td>
                    <td className="px-5 py-3">
                      <span className="flex items-center gap-1.5">
                        {statusIcon(row.status)}
                        <span className="capitalize">{row.status}</span>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
