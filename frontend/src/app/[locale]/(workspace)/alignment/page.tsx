"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { get, post } from "@/lib/api";
import { useWorkspaceStore } from "@/stores/workspaceStore";
import { useAuthStore } from "@/stores/authStore";
import { cn } from "@/lib/utils";

interface DimensionScore {
  dimension: string;
  student_value: number;
  parent_avg: number;
  agreement: boolean;
  diff: number;
}

interface SharedPriorityCollege {
  college_id: string;
  name: string;
  college_type: string | null;
  district: string | null;
  naac_grade: string | null;
  tuition_annual: number | null;
  median_placement_lpa: number | null;
  bridge_reason: string;
}

interface AlignmentDashboard {
  workspace_id: string;
  student_preferences: Record<string, number> | null;
  parent_preferences: Array<{ user_id: string; preferences: Record<string, number> }>;
  alignment_score: number | null;
  dimension_scores: DimensionScore[];
  both_submitted: boolean;
  trade_off_analysis: string[];
  shared_priority_colleges: SharedPriorityCollege[];
  disclaimer: string;
}

interface MediationResponse {
  student_summary: string;
  parent_summary: string;
  compromises: string[];
  citations: Array<{ source: string; year?: number }>;
}

const DIMENSIONS = [
  { key: "branch_interest", icon: "💻", labelKey: "branch_interest" },
  { key: "location_flexibility", icon: "📍", labelKey: "location_flexibility" },
  { key: "budget_priority", icon: "💰", labelKey: "budget_priority" },
  { key: "placement_focus", icon: "📈", labelKey: "placement_focus" },
  { key: "higher_education", icon: "🎓", labelKey: "higher_education" },
  { key: "job_stability", icon: "🛡️", labelKey: "job_stability" },
  { key: "startup_openness", icon: "🚀", labelKey: "startup_openness" },
  { key: "prestige_weight", icon: "🏛️", labelKey: "prestige_weight" },
];

export default function AlignmentPage() {
  const t = useTranslations("alignment");
  const { workspace } = useWorkspaceStore();
  const { user } = useAuthStore();
  const qc = useQueryClient();

  // Submission Form State
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [formPrefs, setFormPrefs] = useState<Record<string, number>>({
    branch_interest: 4,
    location_flexibility: 3,
    budget_priority: 4,
    placement_focus: 5,
    higher_education: 2,
    job_stability: 4,
    startup_openness: 3,
    prestige_weight: 4,
  });

  // Mediation state
  const [activeConflict, setActiveConflict] = useState<string | null>(null);
  const [mediationResult, setMediationResult] = useState<MediationResponse | null>(null);

  const { data: dashboard, isLoading } = useQuery({
    queryKey: ["alignment", workspace?.id],
    queryFn: () => get<AlignmentDashboard>(`/alignment/${workspace?.id}/dashboard`),
    enabled: !!workspace?.id,
  });

  const submitMutation = useMutation({
    mutationFn: () =>
      post(`/alignment/${workspace?.id}/preferences`, { preferences: formPrefs }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["alignment", workspace?.id] });
      setIsFormOpen(false);
    },
  });

  const mediateMutation = useMutation({
    mutationFn: (conflictDim: string) =>
      post<MediationResponse>(`/alignment/${workspace?.id}/mediate`, {
        conflict_dimension: conflictDim,
        additional_context: `Student score vs Parent score on ${conflictDim}`,
      }),
    onSuccess: (data) => setMediationResult(data),
  });

  if (!workspace) {
    return (
      <div className="max-w-4xl mx-auto p-8 text-center text-muted-foreground">
        <p className="text-4xl mb-3">🤝</p>
        <p className="font-medium text-lg">No family workspace active.</p>
        <p className="text-sm mt-1">Please select or create a workspace from the Dashboard to collaborate.</p>
      </div>
    );
  }

  const role = user?.role === "parent" ? "parent" : "student";

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-3xl">🤝</span>
            <h1 className="text-2xl font-bold text-gray-900">{t("title")}</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">{t("subtitle")}</p>
        </div>

        <button
          onClick={() => setIsFormOpen(!isFormOpen)}
          className="rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm px-4 py-2.5 shadow-sm transition"
        >
          {isFormOpen ? "Cancel Editing" : t("submitPrefsButton")}
        </button>
      </div>

      {/* Preference Form Modal / Accordion */}
      {isFormOpen && (
        <div className="rounded-2xl border border-brand-200 bg-white p-6 shadow-md space-y-6 animate-in slide-in-from-top-4">
          <div className="flex items-center justify-between border-b pb-3">
            <div>
              <h2 className="text-lg font-bold text-gray-900">
                Rate Your Priorities ({role === "parent" ? "Parent / Guardian" : "Student"})
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Rate each dimension on a scale of 1 (Low Priority) to 5 (High Priority).
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {DIMENSIONS.map((dim) => (
              <div key={dim.key} className="space-y-2 bg-gray-50 p-4 rounded-xl border border-gray-100">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-gray-800 flex items-center gap-1.5">
                    <span>{dim.icon}</span>
                    {t(`dimensions.${dim.labelKey}` as "dimensions.branch_interest")}
                  </span>
                  <span className="text-sm font-bold text-brand-600">
                    {formPrefs[dim.key] ?? 3} / 5
                  </span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="5"
                  step="1"
                  value={formPrefs[dim.key] ?? 3}
                  onChange={(e) =>
                    setFormPrefs({ ...formPrefs, [dim.key]: parseInt(e.target.value) })
                  }
                  className="w-full accent-brand-600 h-2 bg-gray-200 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-muted-foreground">
                  <span>1 (Low)</span>
                  <span>3 (Moderate)</span>
                  <span>5 (High)</span>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t">
            <button
              onClick={() => setIsFormOpen(false)}
              className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
            >
              Cancel
            </button>
            <button
              onClick={() => submitMutation.mutate()}
              disabled={submitMutation.isPending}
              className="px-6 py-2 text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-lg disabled:opacity-60 transition"
            >
              {submitMutation.isPending ? "Saving..." : "Save My Priorities"}
            </button>
          </div>
        </div>
      )}

      {/* Main Dashboard Display */}
      {isLoading ? (
        <div className="py-20 text-center space-y-3">
          <div className="animate-spin text-4xl inline-block">🔄</div>
          <p className="text-muted-foreground text-sm font-medium">Computing family alignment metrics…</p>
        </div>
      ) : !dashboard?.both_submitted ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50/60 p-8 text-center space-y-4">
          <span className="text-5xl block">⚖️</span>
          <h2 className="text-xl font-bold text-amber-900">{t("bothNeeded")}</h2>
          <p className="text-sm text-amber-800 max-w-md mx-auto">
            {dashboard?.student_preferences
              ? "Student priorities are recorded. An invited parent or guardian needs to rate their preferences to calculate alignment."
              : "Parent priorities are recorded. The student needs to rate their preferences to calculate alignment."}
          </p>
          <button
            onClick={() => setIsFormOpen(true)}
            className="rounded-lg bg-amber-700 hover:bg-amber-800 text-white font-semibold text-sm px-5 py-2.5 transition"
          >
            {t("submitPrefsButton")}
          </button>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Top Score Banner */}
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-6">
              <div className="relative flex items-center justify-center w-24 h-24 rounded-full border-4 border-brand-500 bg-brand-50/30 flex-shrink-0">
                <div className="text-center">
                  <span className="text-2xl font-black text-brand-700">
                    {Math.round(dashboard.alignment_score ?? 0)}%
                  </span>
                  <p className="text-[10px] text-brand-900 font-semibold uppercase tracking-wider">Match</p>
                </div>
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">{t("alignmentScore")}</h2>
                <p className="text-sm text-muted-foreground mt-1">
                  Based on normalized cosine similarity across all 8 family decision dimensions.
                </p>
                <div className="flex items-center gap-3 mt-2 text-xs">
                  <span className="inline-flex items-center gap-1 font-medium text-green-700 bg-green-50 px-2 py-0.5 rounded border border-green-200">
                    ● {dashboard.dimension_scores.filter((d) => d.agreement).length} Agreed
                  </span>
                  <span className="inline-flex items-center gap-1 font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                    ▲ {dashboard.dimension_scores.filter((d) => !d.agreement).length} For Discussion
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={() => setIsFormOpen(true)}
              className="text-xs font-semibold text-brand-600 hover:underline border border-brand-200 bg-brand-50/50 px-4 py-2 rounded-lg"
            >
              Update My Ratings
            </button>
          </div>

          {/* Side-by-Side Dimension Comparison Table */}
          <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden shadow-sm">
            <div className="border-b px-6 py-4 bg-gray-50 flex items-center justify-between">
              <h3 className="font-bold text-gray-900">Side-by-Side Dimension Analysis</h3>
              <span className="text-xs text-muted-foreground">Student vs Family Average</span>
            </div>

            <div className="divide-y divide-gray-100">
              {dashboard.dimension_scores.map((dim) => {
                const meta = DIMENSIONS.find((d) => d.key === dim.dimension);
                return (
                  <div key={dim.dimension} className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-gray-50/50 transition">
                    <div className="w-full md:w-1/3">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{meta?.icon ?? "📌"}</span>
                        <p className="font-semibold text-sm text-gray-900">
                          {t(`dimensions.${dim.dimension}` as "dimensions.branch_interest")}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {dim.agreement ? (
                          <span className="text-[11px] bg-green-100 text-green-800 font-semibold px-2 py-0.5 rounded-full">
                            ✓ {t("agree")}
                          </span>
                        ) : (
                          <span className="text-[11px] bg-amber-100 text-amber-800 font-semibold px-2 py-0.5 rounded-full">
                            ⚠️ {t("conflict")} (Gap: {dim.diff})
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Bars Comparison */}
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-3 text-xs">
                        <span className="w-16 font-medium text-gray-600">Student:</span>
                        <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
                          <div
                            className="bg-brand-600 h-full rounded-full transition-all"
                            style={{ width: `${(dim.student_value / 5) * 100}%` }}
                          />
                        </div>
                        <span className="w-8 font-bold text-right text-brand-700">{dim.student_value}/5</span>
                      </div>

                      <div className="flex items-center gap-3 text-xs">
                        <span className="w-16 font-medium text-gray-600">Parent:</span>
                        <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
                          <div
                            className="bg-indigo-500 h-full rounded-full transition-all"
                            style={{ width: `${(dim.parent_avg / 5) * 100}%` }}
                          />
                        </div>
                        <span className="w-8 font-bold text-right text-indigo-700">{dim.parent_avg}/5</span>
                      </div>
                    </div>

                    {/* AI Mediation Trigger */}
                    {!dim.agreement && (
                      <div className="md:w-36 text-right flex-shrink-0">
                        <button
                          onClick={() => {
                            setActiveConflict(dim.dimension);
                            mediateMutation.mutate(dim.dimension);
                          }}
                          className="rounded-lg bg-brand-50 hover:bg-brand-100 text-brand-700 border border-brand-200 text-xs font-semibold px-3 py-1.5 transition"
                        >
                          🤝 AI Mediation
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* AI Mediation Result Modal / Section */}
          {activeConflict && (
            <div className="rounded-2xl border border-brand-300 bg-brand-50/40 p-6 space-y-4 shadow-sm animate-in fade-in">
              <div className="flex items-center justify-between border-b border-brand-200 pb-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">🤖</span>
                  <h3 className="text-lg font-bold text-brand-950">
                    AI Mediator: {activeConflict.replace(/_/g, " ").toUpperCase()}
                  </h3>
                </div>
                <button
                  onClick={() => {
                    setActiveConflict(null);
                    setMediationResult(null);
                  }}
                  className="text-gray-400 hover:text-gray-700 text-sm font-semibold"
                >
                  ✕ Close
                </button>
              </div>

              {mediateMutation.isPending ? (
                <div className="py-8 text-center space-y-2">
                  <div className="animate-spin text-3xl inline-block">✨</div>
                  <p className="text-xs font-medium text-brand-800">
                    Synthesizing impartial perspective and compromises…
                  </p>
                </div>
              ) : mediationResult ? (
                <div className="space-y-4 text-sm">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-white p-4 rounded-xl border border-brand-100 space-y-1">
                      <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                        {t("studentSummary")}
                      </p>
                      <p className="text-gray-800">{mediationResult.student_summary}</p>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-brand-100 space-y-1">
                      <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                        {t("parentSummary")}
                      </p>
                      <p className="text-gray-800">{mediationResult.parent_summary}</p>
                    </div>
                  </div>

                  <div className="bg-white p-4 rounded-xl border border-brand-100 space-y-2">
                    <p className="text-xs font-bold text-brand-900 uppercase tracking-wider">
                      💡 {t("compromises")}
                    </p>
                    <ul className="list-disc list-inside space-y-1 text-gray-800">
                      {mediationResult.compromises.map((comp, idx) => (
                        <li key={idx} className="leading-relaxed">{comp}</li>
                      ))}
                    </ul>
                  </div>

                  {mediationResult.citations.length > 0 && (
                    <div className="flex flex-wrap items-center gap-2 pt-2 text-xs text-muted-foreground">
                      <span className="font-semibold text-gray-700">Verified Sources:</span>
                      {mediationResult.citations.map((c, i) => (
                        <span key={i} className="rounded bg-gray-100 px-2 py-0.5 border text-gray-700">
                          {c.source} {c.year ? `(${c.year})` : ""}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          )}

          {/* Trade-Off Explanations */}
          {dashboard.trade_off_analysis.length > 0 && (
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-3">
              <h3 className="font-bold text-gray-900 flex items-center gap-2 text-base">
                <span>💬</span> Key Trade-Offs for Family Discussion
              </h3>
              <div className="space-y-2">
                {dashboard.trade_off_analysis.map((item, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-gray-50 border border-gray-100 text-sm text-gray-800 leading-relaxed">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Colleges Bridging Family Priorities */}
          {dashboard.shared_priority_colleges.length > 0 && (
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
              <div>
                <h3 className="font-bold text-gray-900 flex items-center gap-2 text-base">
                  <span>🏛️</span> Colleges Satisfying Shared Family Priorities
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Institutional options identified by FamPath that bridge budget comfort and placement expectations.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {dashboard.shared_priority_colleges.map((col) => (
                  <div key={col.college_id} className="rounded-xl border border-gray-200 p-4 bg-gray-50/50 space-y-3 hover:border-brand-300 transition">
                    <div>
                      <p className="font-bold text-sm text-gray-900">{col.name}</p>
                      <p className="text-xs text-muted-foreground capitalize">
                        {[col.district, col.college_type].filter(Boolean).join(" · ")}
                      </p>
                    </div>

                    <div className="flex justify-between text-xs py-1 border-t border-b border-gray-200/60">
                      <div>
                        <span className="text-gray-500 block text-[10px]">Tuition (Yr)</span>
                        <span className="font-semibold text-gray-800">
                          {col.tuition_annual ? `₹${col.tuition_annual.toLocaleString("en-IN")}` : "Unlisted"}
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-gray-500 block text-[10px]">Median LPA</span>
                        <span className="font-semibold text-green-700">
                          {col.median_placement_lpa ? `₹${col.median_placement_lpa.toFixed(1)} LPA` : "Unlisted"}
                        </span>
                      </div>
                    </div>

                    <p className="text-xs text-brand-900 bg-brand-50 p-2 rounded-lg font-medium">
                      💡 {col.bridge_reason}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Safety Disclaimer */}
          <div className="rounded-xl bg-amber-50 border border-amber-200 p-4 text-xs text-amber-900 space-y-1">
            <p className="font-bold">⚠️ Decision-Support Disclaimer</p>
            <p>{dashboard.disclaimer}</p>
          </div>
        </div>
      )}
    </div>
  );
}
