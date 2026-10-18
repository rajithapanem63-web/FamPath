"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useTranslations } from "next-intl";
import { useQuery, useMutation } from "@tanstack/react-query";
import { post } from "@/lib/api";
import { useWorkspaceStore } from "@/stores/workspaceStore";
import { cn, type Band } from "@/lib/utils";
import CollegeComparisonModal from "@/components/CollegeComparisonModal";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const schema = z.object({
  exam_type: z.enum(["AP_EAPCET", "TS_EAPCET", "JEE_MAINS", "JEE_ADV"]),
  rank: z.coerce.number().int().min(1).max(500000),
  category: z.enum(["OC", "BC_A", "BC_B", "BC_C", "BC_D", "BC_E", "SC", "ST", "EWS"]),
  gender: z.enum(["male", "female", "other", "any"]).default("any"),
});
type FormValues = z.infer<typeof schema>;

interface ShapFactor {
  feature: string;
  direction: "positive" | "negative";
  contribution: number;
}

interface PredictionItem {
  college_id: string;
  college_name: string;
  branch_code: string;
  branch_name: string;
  band: Band;
  probability: number;
  predicted_closing_rank: number;
  data_year: number;
  shap_factors: ShapFactor[];
  disclaimer: string;
}

interface PredictResponse {
  predictions: PredictionItem[];
  model_version: string;
  data_year_range: string;
}

// Helper to get band color classes
const getBandColors = (band: Band) => {
  const colors = {
    Safe: "border-green-200 bg-green-50/50",
    Target: "border-yellow-200 bg-yellow-50/50",
    Dream: "border-blue-200 bg-blue-50/50",
  };
  return colors[band];
};

// Helper to get band badge colors
const getBandBadgeColors = (band: Band) => {
  const colors = {
    Safe: "bg-green-100 text-green-800 border-green-300",
    Target: "bg-yellow-100 text-yellow-800 border-yellow-300",
    Dream: "bg-blue-100 text-blue-800 border-blue-300",
  };
  return colors[band];
};

export default function PredictPage() {
  const t = useTranslations("prediction");
  const { workspace } = useWorkspaceStore();
  const [submitted, setSubmitted] = useState<FormValues | null>(null);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const [isCompareOpen, setIsCompareOpen] = useState(false);
  const [shortlistFeedback, setShortlistFeedback] = useState<Record<string, string>>({});

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { exam_type: "AP_EAPCET", gender: "any", rank: undefined, category: "OC" },
  });

  const { data, isFetching, error } = useQuery({
    queryKey: ["predict", submitted],
    queryFn: () =>
      submitted ? post<PredictResponse>("/predict/colleges", { ...submitted, filters: {} }) : null,
    enabled: !!submitted,
  });

  const addShortlistMutation = useMutation({
    mutationFn: (p: PredictionItem) =>
      post(`/shortlist/${workspace?.id}`, {
        college_id: p.college_id,
        program_id: "00000000-0000-0000-0000-000000000000",
        prediction_snapshot: {
          college_name: p.college_name,
          branch_name: p.branch_name,
          band: p.band,
          probability: p.probability,
        },
      }),
    onSuccess: (_, p) => {
      setShortlistFeedback((prev) => ({ ...prev, [p.college_id]: "✓ Added to Shortlist!" }));
      setTimeout(() => {
        setShortlistFeedback((prev) => {
          const next = { ...prev };
          delete next[p.college_id];
          return next;
        });
      }, 3000);
    },
  });

  function toggleCompare(collegeId: string) {
    if (selectedForCompare.includes(collegeId)) {
      setSelectedForCompare(selectedForCompare.filter((id) => id !== collegeId));
    } else {
      if (selectedForCompare.length < 4) {
        setSelectedForCompare([...selectedForCompare, collegeId]);
      }
    }
  }

  function onSubmit(values: FormValues) {
    setSubmitted(values);
  }

  const grouped = data
    ? {
        Safe: data.predictions.filter((p) => p.band === "Safe"),
        Target: data.predictions.filter((p) => p.band === "Target"),
        Dream: data.predictions.filter((p) => p.band === "Dream"),
      }
    : null;

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-6 space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">{t("title")}</h1>
        <p className="text-muted-foreground text-sm max-w-3xl mx-auto">{t("subtitle")}</p>
      </div>

      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Enter Your Details</CardTitle>
          <CardDescription>
            We'll compare your rank against historical cutoff data to show your admission chances.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Exam Type */}
            <div className="space-y-2">
              <Label htmlFor="exam_type">{t("examLabel")}</Label>
              <select
                id="exam_type"
                {...register("exam_type")}
                className="w-full rounded-lg border border-input bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="AP_EAPCET">AP EAPCET</option>
                <option value="TS_EAPCET">TS EAPCET</option>
                <option value="JEE_MAINS">JEE Mains</option>
                <option value="JEE_ADV">JEE Advanced</option>
              </select>
            </div>

            {/* Rank */}
            <div className="space-y-2">
              <Label htmlFor="rank">{t("rankLabel")}</Label>
              <Input
                id="rank"
                type="number"
                {...register("rank")}
                placeholder={t("rankPlaceholder")}
                aria-invalid={!!errors.rank}
                className="w-full"
              />
              {errors.rank && (
                <p className="text-xs text-red-600">{errors.rank.message}</p>
              )}
            </div>

            {/* Category */}
            <div className="space-y-2">
              <Label htmlFor="category">{t("categoryLabel")}</Label>
              <select
                id="category"
                {...register("category")}
                className="w-full rounded-lg border border-input bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {["OC", "BC_A", "BC_B", "BC_C", "BC_D", "BC_E", "SC", "ST", "EWS"].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            {/* Submit Button */}
            <div className="flex items-end">
              <Button
                type="submit"
                disabled={isSubmitting || isFetching}
                className="w-full"
              >
                {isFetching ? "Searching..." : t("predictButton")}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Explanation of Categories */}
      <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-base">{t("explainCategories.title")}</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="bg-white rounded-lg p-4 border border-green-200 space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-2xl">✅</span>
              <h3 className="font-bold text-green-800">{t("explainCategories.safeTitle")}</h3>
            </div>
            <p className="text-gray-700">{t("explainCategories.safeDesc")}</p>
          </div>

          <div className="bg-white rounded-lg p-4 border border-yellow-200 space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-2xl">🎯</span>
              <h3 className="font-bold text-yellow-800">{t("explainCategories.targetTitle")}</h3>
            </div>
            <p className="text-gray-700">{t("explainCategories.targetDesc")}</p>
          </div>

          <div className="bg-white rounded-lg p-4 border border-blue-200 space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-2xl">⭐</span>
              <h3 className="font-bold text-blue-800">{t("explainCategories.dreamTitle")}</h3>
            </div>
            <p className="text-gray-700">{t("explainCategories.dreamDesc")}</p>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {grouped && (
        <div className="space-y-6">
          {/* Summary */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex flex-wrap gap-4">
                  {(["Safe", "Target", "Dream"] as Band[]).map((band) => (
                    <div key={band} className={cn("rounded-lg px-4 py-2 border font-semibold", getBandBadgeColors(band))}>
                      {t(`summary.${band.toLowerCase() as 'safe'}`, { count: grouped[band].length })}
                    </div>
                  ))}
                </div>

                {selectedForCompare.length >= 2 && (
                  <Button
                    onClick={() => setIsCompareOpen(true)}
                    variant="default"
                    className="animate-pulse"
                  >
                    ⚖️ Compare ({selectedForCompare.length}) Colleges
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* College Cards by Band */}
          {(["Safe", "Target", "Dream"] as Band[]).map(
            (band) =>
              grouped[band].length > 0 && (
                <div key={band} className="space-y-4">
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    {band === "Safe" && <span>✅</span>}
                    {band === "Target" && <span>🎯</span>}
                    {band === "Dream" && <span>⭐</span>}
                    {t(`resultCard.${band.toLowerCase()}Label` as 'resultCard.safeLabel')} ({grouped[band].length})
                  </h2>
                  <div className="grid gap-4 md:grid-cols-2">
                    {grouped[band].map((p) => (
                      <PredictionCard
                        key={`${p.college_id}-${p.branch_code}`}
                        prediction={p}
                        t={t}
                        band={band}
                        studentRank={submitted?.rank}
                        isCompared={selectedForCompare.includes(p.college_id)}
                        onToggleCompare={() => toggleCompare(p.college_id)}
                        onAddToShortlist={() => addShortlistMutation.mutate(p)}
                        shortlistStatus={shortlistFeedback[p.college_id]}
                        hasWorkspace={!!workspace}
                      />
                    ))}
                  </div>
                </div>
              )
          )}
        </div>
      )}

      {/* Empty State */}
      {submitted && !isFetching && data?.predictions.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <span className="text-6xl block mb-4">🔍</span>
            <p className="text-lg font-semibold text-gray-900 mb-2">{t("noResults")}</p>
            <p className="text-sm text-muted-foreground">{t("insufficientData")}</p>
          </CardContent>
        </Card>
      )}

      {/* College Comparison Modal */}
      {data && (
        <CollegeComparisonModal
          isOpen={isCompareOpen}
          onClose={() => setIsCompareOpen(false)}
          availableColleges={data.predictions.map((p) => ({
            college_id: p.college_id,
            college_name: p.college_name.replace(" (SEED DATA)", ""),
            branch_name: p.branch_name,
          }))}
          initialSelectedIds={selectedForCompare}
        />
      )}
    </div>
  );
}

function PredictionCard({
  prediction: p,
  t,
  band,
  studentRank,
  isCompared,
  onToggleCompare,
  onAddToShortlist,
  shortlistStatus,
  hasWorkspace,
}: {
  prediction: PredictionItem;
  t: ReturnType<typeof useTranslations<"prediction">>;
  band: Band;
  studentRank?: number;
  isCompared: boolean;
  onToggleCompare: () => void;
  onAddToShortlist: () => void;
  shortlistStatus?: string;
  hasWorkspace: boolean;
}) {
  const [showWhy, setShowWhy] = useState(false);

  // Remove (SEED DATA) from college name for display
  const displayName = p.college_name.replace(" (SEED DATA)", "");

  // Determine admission outlook text
  const getOutlookText = () => {
    if (band === "Safe") return t("resultCard.strongChance");
    if (band === "Target") return t("resultCard.competitive");
    return t("resultCard.challenging");
  };

  return (
    <Card className={cn("transition-all hover:shadow-md", getBandColors(band))}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base font-bold text-gray-900 truncate">
              {displayName}
            </CardTitle>
            <CardDescription className="text-sm mt-1">
              {p.branch_name}
            </CardDescription>
          </div>
          <span className={cn("rounded-full px-3 py-1 text-xs font-bold border shrink-0", getBandBadgeColors(band))}>
            {t(`resultCard.${band.toLowerCase()}Label` as 'resultCard.safeLabel')}
          </span>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Admission Outlook */}
        <div className="bg-white/70 rounded-lg p-3 space-y-2">
          <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
            {t("resultCard.admissionOutlook")}
          </p>
          <p className="text-sm font-medium text-gray-900">{getOutlookText()}</p>
        </div>

        {/* Key Details */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="space-y-1">
            <p className="text-muted-foreground">{t("resultCard.historicalClosingRank")}</p>
            <p className="font-bold text-base text-gray-900">
              {p.predicted_closing_rank.toLocaleString("en-IN")}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground">{t("resultCard.dataYear")}</p>
            <p className="font-bold text-base text-gray-900">{p.data_year}</p>
          </div>
        </div>

        {/* Why This Band */}
        <button
          onClick={() => setShowWhy(!showWhy)}
          className="text-xs text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-1 font-medium"
          aria-expanded={showWhy}
        >
          {t("resultCard.whyThisBand")} {showWhy ? "▲" : "▼"}
        </button>

        {showWhy && studentRank && (
          <div className="text-xs bg-white rounded-lg p-3 border space-y-2">
            <div className="space-y-1">
              <div className="flex justify-between items-center py-1">
                <span className="text-gray-600 font-medium">Your Rank:</span>
                <span className="font-bold text-gray-900">{studentRank.toLocaleString("en-IN")}</span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-gray-600 font-medium">Historical Closing Rank:</span>
                <span className="font-bold text-gray-900">{p.predicted_closing_rank.toLocaleString("en-IN")}</span>
              </div>
              <div className="flex justify-between items-center py-1 border-t pt-2 mt-2">
                <span className="text-gray-600 font-medium">Rank Comparison:</span>
                <span className={cn(
                  "font-bold",
                  studentRank < p.predicted_closing_rank ? "text-green-700" : "text-red-700"
                )}>
                  {studentRank < p.predicted_closing_rank 
                    ? `${((p.predicted_closing_rank - studentRank) / p.predicted_closing_rank * 100).toFixed(1)}% better`
                    : `${((studentRank - p.predicted_closing_rank) / p.predicted_closing_rank * 100).toFixed(1)}% below`
                  }
                </span>
              </div>
            </div>
            
            <div className="pt-2 border-t">
              <p className="text-gray-700 leading-relaxed">
                {band === "Safe" && `Your rank is significantly better (lower number) than the historical closing rank. Based on past data, you have a strong chance of admission to this program.`}
                {band === "Target" && `Your rank is competitive with the historical closing rank. Admission is realistic, though not guaranteed. This is a good target option to include in your choices.`}
                {band === "Dream" && `Your rank is below (higher number than) the historical closing rank. While admission may be more challenging, it's not impossible. Consider this as an aspirational choice alongside safer options.`}
              </p>
            </div>
            
            <div className="pt-2 border-t">
              <p className="text-xs text-gray-500 italic">
                Data Year: {p.data_year} | Based on {p.data_year} counselling closing rank
              </p>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-2 border-t gap-2">
          <label className="flex items-center gap-2 cursor-pointer text-xs text-gray-700 hover:text-blue-600 select-none">
            <input
              type="checkbox"
              checked={isCompared}
              onChange={onToggleCompare}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="font-medium">{t("resultCard.compare")}</span>
          </label>

          {hasWorkspace && (
            <Button
              onClick={onAddToShortlist}
              variant={shortlistStatus ? "outline" : "default"}
              size="sm"
              className={cn(
                "text-xs",
                shortlistStatus && "bg-green-100 text-green-700 hover:bg-green-100"
              )}
            >
              {shortlistStatus ?? `+ ${t("resultCard.addToShortlist")}`}
            </Button>
          )}
        </div>

        {/* Disclaimer */}
        <p className="text-xs text-muted-foreground italic pt-2 border-t">
          {t("resultCard.disclaimer")}
        </p>
      </CardContent>
    </Card>
  );
}
