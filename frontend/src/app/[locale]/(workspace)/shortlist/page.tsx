"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { get, post, del } from "@/lib/api";
import { useWorkspaceStore } from "@/stores/workspaceStore";
import { cn } from "@/lib/utils";
import CollegeComparisonModal, { type CompareTarget } from "@/components/CollegeComparisonModal";

interface ShortlistItem {
  id: string;
  college_id: string;
  program_id: string;
  added_by: string;
  is_final_choice: boolean;
  cost_snapshot: Record<string, unknown> | null;
  prediction_snapshot: Record<string, unknown> | null;
  votes: Array<{ user_id: string; vote: number; comment: string | null }>;
  created_at: string;
}

export default function ShortlistPage() {
  const t = useTranslations("shortlist");
  const { workspace } = useWorkspaceStore();
  const qc = useQueryClient();
  const [isCompareOpen, setIsCompareOpen] = useState(false);

  const { data: items = [], isLoading } = useQuery({
    queryKey: ["shortlist", workspace?.id],
    queryFn: () => get<ShortlistItem[]>(`/shortlist/${workspace?.id}`),
    enabled: !!workspace?.id,
  });

  const removeMutation = useMutation({
    mutationFn: (itemId: string) =>
      del<{ message: string }>(`/shortlist/${workspace?.id}/${itemId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shortlist"] }),
  });

  const voteMutation = useMutation({
    mutationFn: ({ itemId, vote }: { itemId: string; vote: number }) =>
      post<{ message: string }>(`/shortlist/${workspace?.id}/${itemId}/vote`, { vote }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shortlist"] }),
  });

  const finalMutation = useMutation({
    mutationFn: (itemId: string) =>
      post<{ message: string }>(`/shortlist/${workspace?.id}/${itemId}/final`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shortlist"] }),
  });

  if (!workspace) {
    return <div className="p-6 text-muted-foreground">No workspace selected.</div>;
  }

  const comparisonTargets: CompareTarget[] = items.map((item) => {
    const snap = item.prediction_snapshot as { college_name?: string; branch_name?: string } | null;
    return {
      college_id: item.college_id,
      program_id: item.program_id,
      college_name: snap?.college_name ?? `College ${item.college_id.slice(0, 8)}`,
      branch_name: snap?.branch_name ?? "Engineering",
    };
  });

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("title")}</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Your family&apos;s saved college options and voting records
          </p>
        </div>
        <div className="flex items-center gap-3">
          {items.length >= 2 && (
            <button
              onClick={() => setIsCompareOpen(true)}
              className="flex items-center gap-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold px-3 py-2 shadow-sm transition"
            >
              <span>⚖️</span> Compare Shortlist
            </button>
          )}
          <span className="text-sm text-muted-foreground">{items.length} / 20</span>
        </div>
      </div>

      {isLoading && <p className="text-muted-foreground text-sm">{useTranslations("common")("loading")}</p>}

      {!isLoading && items.length === 0 && (
        <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-12 text-center">
          <p className="text-4xl mb-3">📋</p>
          <p className="text-muted-foreground">{t("empty")}</p>
        </div>
      )}

      <div className="space-y-4">
        {items.map((item) => {
          const upVotes = item.votes.filter((v) => v.vote === 1).length;
          const downVotes = item.votes.filter((v) => v.vote === -1).length;
          const snapshot = item.prediction_snapshot as { college_name?: string; branch_name?: string; band?: string } | null;

          return (
            <div
              key={item.id}
              className={cn(
                "rounded-xl border bg-white p-4 space-y-3",
                item.is_final_choice && "border-green-400 bg-green-50"
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold">
                    {snapshot?.college_name ?? `College ${item.college_id.slice(0, 8)}`}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {snapshot?.branch_name ?? `Program ${item.program_id.slice(0, 8)}`}
                  </p>
                  {snapshot?.band && (
                    <span className={cn(
                      "inline-block text-xs rounded-full px-2 py-0.5 mt-1 border font-medium",
                      snapshot.band === "Safe" && "band-safe",
                      snapshot.band === "Target" && "band-target",
                      snapshot.band === "Dream" && "band-dream",
                    )}>
                      {snapshot.band}
                    </span>
                  )}
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  {item.is_final_choice && (
                    <span className="text-xs bg-green-100 text-green-700 border border-green-300 rounded-full px-2 py-0.5 font-medium">
                      {t("finalBadge")}
                    </span>
                  )}
                </div>
              </div>

              {/* Votes */}
              <div className="flex items-center gap-3">
                <button
                  onClick={() => voteMutation.mutate({ itemId: item.id, vote: 1 })}
                  className="flex items-center gap-1 text-sm text-green-700 hover:text-green-800"
                  aria-label={t("thumbsUp")}
                >
                  👍 {upVotes}
                </button>
                <button
                  onClick={() => voteMutation.mutate({ itemId: item.id, vote: -1 })}
                  className="flex items-center gap-1 text-sm text-red-700 hover:text-red-800"
                  aria-label={t("thumbsDown")}
                >
                  👎 {downVotes}
                </button>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-1 border-t border-gray-100">
                {!item.is_final_choice && (
                  <button
                    onClick={() => finalMutation.mutate(item.id)}
                    className="text-xs text-brand-600 hover:underline"
                  >
                    {t("markFinal")}
                  </button>
                )}
                <button
                  onClick={() => removeMutation.mutate(item.id)}
                  className="text-xs text-red-600 hover:underline ml-auto"
                >
                  {t("removeButton")}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {items.length >= 20 && (
        <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
          {t("limit")}
        </p>
      )}

      {/* College Comparison Modal */}
      <CollegeComparisonModal
        isOpen={isCompareOpen}
        onClose={() => setIsCompareOpen(false)}
        availableColleges={comparisonTargets}
      />
    </div>
  );
}
