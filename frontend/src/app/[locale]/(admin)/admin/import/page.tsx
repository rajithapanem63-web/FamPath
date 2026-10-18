"use client";

import { useState, useRef } from "react";
import { Upload, CheckCircle, AlertCircle, Clock, FileText } from "lucide-react";

const DATASET_TYPES = [
  { value: "colleges", label: "Colleges", desc: "College master data (name, type, location, NAAC)" },
  { value: "cutoffs", label: "Cutoff Records", desc: "Year-wise rank cutoffs per college, branch, category" },
  { value: "fees", label: "Fee Structures", desc: "Tuition, hostel, transport fees per college/program" },
  { value: "placements", label: "Placement Stats", desc: "Placement percentage, median packages, recruiters" },
  { value: "scholarships", label: "Scholarships", desc: "Scholarship eligibility, amounts, and deadlines" },
];

interface ImportJob {
  job_id: string;
  status: "pending" | "running" | "success" | "failed";
  message?: string;
  record_count?: number;
  errors?: string[];
}

export default function AdminImportPage() {
  const [dataset, setDataset] = useState("colleges");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [job, setJob] = useState<ImportJob | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setJob(null);

    const token = typeof window !== "undefined" ? sessionStorage.getItem("fampath_token") : null;
    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch(`${API_URL}/api/v1/admin/import/${dataset}`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      });
      const data = await res.json();
      if (res.ok) {
        setJob({ job_id: data.job_id, status: "pending", message: "Import queued…" });
        // Poll status
        const jobId = data.job_id;
        const poll = setInterval(async () => {
          try {
            const sr = await fetch(`${API_URL}/api/v1/admin/import/${jobId}`, {
              headers: token ? { Authorization: `Bearer ${token}` } : {},
            });
            const sd = await sr.json();
            setJob({ job_id: jobId, status: sd.status, message: sd.message, record_count: sd.record_count, errors: sd.errors });
            if (sd.status === "success" || sd.status === "failed") clearInterval(poll);
          } catch { clearInterval(poll); }
        }, 2000);
      } else {
        setJob({ job_id: "", status: "failed", message: data.message ?? "Upload failed" });
      }
    } catch (err) {
      setJob({ job_id: "", status: "failed", message: "Network error" });
    } finally {
      setUploading(false);
    }
  }

  const statusIcon = (status: string) => {
    if (status === "success") return <CheckCircle className="h-5 w-5 text-green-500" />;
    if (status === "failed") return <AlertCircle className="h-5 w-5 text-destructive" />;
    return <Clock className="h-5 w-5 text-yellow-500 animate-spin" />;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Data Import</h1>
        <p className="text-muted-foreground mt-1">Upload CSV files to populate college, cutoff, and fee data.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Upload form */}
        <div className="rounded-xl border bg-card p-6 space-y-5">
          <h2 className="font-semibold">Upload CSV</h2>

          {/* Dataset selector */}
          <div>
            <label className="text-sm font-medium block mb-2" htmlFor="dataset-type">Dataset type</label>
            <select
              id="dataset-type"
              value={dataset}
              onChange={(e) => setDataset(e.target.value)}
              className="w-full rounded-lg border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {DATASET_TYPES.map((d) => (
                <option key={d.value} value={d.value}>{d.label}</option>
              ))}
            </select>
            <p className="mt-1.5 text-xs text-muted-foreground">
              {DATASET_TYPES.find(d => d.value === dataset)?.desc}
            </p>
          </div>

          {/* File drop zone */}
          <div
            onClick={() => fileRef.current?.click()}
            className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/30 px-6 py-10 hover:border-primary hover:bg-muted/30 transition-colors"
            role="button"
            aria-label="Click to select CSV file"
          >
            <FileText className="h-10 w-10 text-muted-foreground mb-3" />
            {file ? (
              <p className="text-sm font-medium">{file.name}</p>
            ) : (
              <>
                <p className="text-sm font-medium">Click to select CSV</p>
                <p className="text-xs text-muted-foreground mt-1">Max 10 MB</p>
              </>
            )}
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              className="sr-only"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              aria-label="CSV file input"
            />
          </div>

          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {uploading ? (
              <><Clock className="h-4 w-4 animate-spin" /> Uploading…</>
            ) : (
              <><Upload className="h-4 w-4" /> Import {DATASET_TYPES.find(d => d.value === dataset)?.label}</>
            )}
          </button>
        </div>

        {/* Job status */}
        <div className="rounded-xl border bg-card p-6 space-y-4">
          <h2 className="font-semibold">Import Status</h2>
          {!job ? (
            <div className="py-12 text-center text-muted-foreground">
              <Upload className="mx-auto h-10 w-10 mb-3 opacity-30" />
              <p className="text-sm">No import started yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-3 rounded-lg border p-4">
                {statusIcon(job.status)}
                <div>
                  <p className="font-medium capitalize">{job.status}</p>
                  {job.message && <p className="text-sm text-muted-foreground">{job.message}</p>}
                </div>
              </div>
              {job.record_count !== undefined && (
                <div className="rounded-lg bg-green-50 border border-green-200 p-3 text-sm text-green-800">
                  ✓ {job.record_count.toLocaleString("en-IN")} records imported successfully
                </div>
              )}
              {job.errors && job.errors.length > 0 && (
                <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-3 space-y-1">
                  <p className="text-sm font-medium text-destructive">Errors ({job.errors.length}):</p>
                  {job.errors.slice(0, 5).map((e, i) => (
                    <p key={i} className="text-xs text-destructive/80">{e}</p>
                  ))}
                  {job.errors.length > 5 && <p className="text-xs text-muted-foreground">…and {job.errors.length - 5} more</p>}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* CSV format guide */}
      <div className="rounded-xl border bg-muted/30 p-6">
        <h2 className="font-semibold mb-3">CSV Format Requirements</h2>
        <div className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
          {DATASET_TYPES.map((d) => (
            <div key={d.value} className="rounded-lg bg-background border p-3">
              <p className="font-medium">{d.label}</p>
              <p className="text-xs text-muted-foreground mt-1">{d.desc}</p>
            </div>
          ))}
        </div>
        <p className="text-xs text-muted-foreground mt-3">
          All imports must include: <code className="bg-muted px-1 rounded">source</code>, <code className="bg-muted px-1 rounded">year</code> columns.
          Seed data will be labelled SEED_ automatically in dev.
        </p>
      </div>
    </div>
  );
}
