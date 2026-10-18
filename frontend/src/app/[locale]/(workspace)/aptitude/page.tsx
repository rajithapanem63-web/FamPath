"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery, useMutation } from "@tanstack/react-query";
import { get, post } from "@/lib/api";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

interface Question {
  id: string;
  text: string;
  options: Array<{ value: number; label_en: string }> | null;
  riasec_dimension: string;
}

interface SessionResponse {
  session_id: string;
  questions: Question[];
  total: number;
}

interface AptitudeResult {
  riasec_scores: Record<string, number>;
  branch_fit_scores: Record<string, number>;
  top_branches: Array<{ branch: string; score: number; drivers: string[] }>;
}

const RIASEC_LABELS: Record<string, string> = {
  R: "Realistic", I: "Investigative", A: "Artistic",
  S: "Social", E: "Enterprising", C: "Conventional",
};

const BRANCH_COLORS = ["#2563EB", "#16a34a", "#d97706", "#7c3aed", "#dc2626", "#0891b2"];

const BRANCH_INFO = {
  CSE: { icon: "💻", color: "bg-blue-50 border-blue-200" },
  "AI-DS": { icon: "🤖", color: "bg-purple-50 border-purple-200" },
  ECE: { icon: "📡", color: "bg-green-50 border-green-200" },
  EEE: { icon: "⚡", color: "bg-yellow-50 border-yellow-200" },
  MECH: { icon: "⚙️", color: "bg-orange-50 border-orange-200" },
  CIVIL: { icon: "🏗️", color: "bg-gray-50 border-gray-200" },
};

export default function AptitudePage() {
  const t = useTranslations("aptitude");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<AptitudeResult | null>(null);
  const [showReview, setShowReview] = useState(false);

  // Check for existing result
  const { data: existingResult } = useQuery({
    queryKey: ["aptitude", "latest"],
    queryFn: () => get<AptitudeResult | null>("/aptitude/results/latest"),
  });

  // Start quiz
  const startMutation = useMutation({
    mutationFn: () => get<SessionResponse>("/aptitude/questions"),
    onSuccess: (data) => {
      console.log("Quiz started successfully:", data);
      setSessionId(data.session_id);
      setCurrentIdx(0);
      setAnswers({});
      setShowReview(false);
    },
    onError: (error: any) => {
      console.error("Failed to start quiz:", error);
      // Check if it's an authentication error
      if (error?.response?.status === 401 || error?.message?.includes("401")) {
        // Redirect to sign in
        window.location.href = "/en/sign-in?redirect=/en/aptitude";
      }
    },
  });

  // Submit quiz
  const submitMutation = useMutation({
    mutationFn: () =>
      post<AptitudeResult>(`/aptitude/sessions/${sessionId}/submit`),
    onSuccess: (data) => setResult(data),
  });

  // Save responses
  const saveResponses = async (questionId: string, value: number) => {
    const newAnswers = { ...answers, [questionId]: value };
    setAnswers(newAnswers);

    await post(`/aptitude/sessions/${sessionId}/responses`, {
      responses: [{ question_id: questionId, value }],
    });
  };

  const handleNext = () => {
    const questions = startMutation.data?.questions ?? [];
    if (currentIdx < questions.length - 1) {
      setCurrentIdx(currentIdx + 1);
    } else {
      setShowReview(true);
    }
  };

  const handlePrevious = () => {
    if (currentIdx > 0) {
      setCurrentIdx(currentIdx - 1);
    }
  };

  const handleSubmit = async () => {
    await submitMutation.mutateAsync();
  };

  const displayResult = result ?? (existingResult || null);
  const questions = startMutation.data?.questions ?? [];
  const currentQuestion = questions[currentIdx];

  // ── Results view ───────────────────────────────────────────────────────────
  if (displayResult && !sessionId) {
    const radarData = Object.entries(displayResult.riasec_scores).map(([dim, score]) => ({
      subject: RIASEC_LABELS[dim] ?? dim,
      score,
    }));

    const barData = Object.entries(displayResult.branch_fit_scores)
      .map(([branch, score]) => ({ branch, score }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 8);

    return (
      <div className="max-w-5xl mx-auto p-4 sm:p-6 space-y-6">
        {/* Header */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 text-green-600 text-3xl mb-4">
            🎯
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">{t("results.title")}</h1>
          <p className="text-muted-foreground mt-2 max-w-2xl mx-auto">{t("results.subtitle")}</p>
        </div>

        {/* Top Recommended Branches - Featured */}
        <Card className="border-2 border-brand-200 bg-gradient-to-br from-brand-50 to-white">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">🌟</span>
              {t("results.topBranchesTitle")}
            </CardTitle>
            <CardDescription>{t("results.topBranchesDesc")}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {displayResult.top_branches.slice(0, 3).map((b, i) => {
                const branchKey = b.branch.replace(/[^A-Z]/g, "");
                const branchIcon = BRANCH_INFO[branchKey as keyof typeof BRANCH_INFO]?.icon || "📚";
                return (
                  <div key={b.branch} className="rounded-xl border-2 border-brand-300 bg-white p-4 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-3xl">{branchIcon}</span>
                        <div className="flex items-center gap-1">
                          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-brand-600 text-white text-xs font-bold">
                            {i + 1}
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-brand-700">{b.score}</div>
                        <div className="text-xs text-muted-foreground">/100</div>
                      </div>
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-2 text-sm sm:text-base">{b.branch}</h3>
                    <div className="flex flex-wrap gap-1">
                      {b.drivers.map((d) => (
                        <span key={d} className="inline-flex items-center px-2 py-1 rounded-full bg-brand-100 text-brand-700 text-xs font-medium">
                          {RIASEC_LABELS[d] ?? d}
                        </span>
                      ))}
                    </div>
                    <p className="text-xs text-muted-foreground mt-3 leading-relaxed">
                      {t(`results.branchMatch.${b.branch.toLowerCase().replace(/[^a-z]/g, "")}`, { defaultValue: t("results.matchExplanation", { drivers: b.drivers.map(d => RIASEC_LABELS[d] ?? d).join(", ") }) })}
                    </p>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Analysis Cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* RIASEC Profile */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <span>📊</span>
                {t("results.riasecTitle")}
              </CardTitle>
              <CardDescription>{t("results.riasecDesc")}</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#e5e7eb" />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: "#6b7280" }} />
                  <Radar dataKey="score" stroke="#2563EB" fill="#2563EB" fillOpacity={0.4} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                {Object.entries(displayResult.riasec_scores).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([dim, score]) => (
                  <div key={dim} className="flex items-center justify-between px-3 py-2 rounded-lg bg-gray-50">
                    <span className="font-medium text-gray-700">{RIASEC_LABELS[dim]}</span>
                    <span className="font-bold text-brand-600">{score}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Branch Fit Scores */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <span>📈</span>
                {t("results.branchFitTitle")}
              </CardTitle>
              <CardDescription>{t("results.branchFitDesc")}</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={barData} layout="vertical" margin={{ left: 10, right: 10 }}>
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} stroke="#9ca3af" />
                  <YAxis dataKey="branch" type="category" tick={{ fontSize: 11 }} width={50} stroke="#9ca3af" />
                  <Tooltip 
                    formatter={(v: number) => [`${v}/100`, "Score"]}
                    contentStyle={{ borderRadius: "8px", border: "1px solid #e5e7eb" }}
                  />
                  <Bar dataKey="score" radius={[0, 6, 6, 0]}>
                    {barData.map((_, i) => (
                      <Cell key={i} fill={BRANCH_COLORS[i % BRANCH_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center pt-4">
          <Button
            variant="outline"
            onClick={() => { setSessionId(null); setResult(null); startMutation.reset(); }}
            className="w-full sm:w-auto"
          >
            🔄 {t("results.retakeButton")}
          </Button>
          <Button
            onClick={() => window.location.href = "/en/predict"}
            className="w-full sm:w-auto bg-brand-600 hover:bg-brand-700"
          >
            🎓 {t("results.viewPrediction")}
          </Button>
        </div>
      </div>
    );
  }

  // ── Review screen ──────────────────────────────────────────────────────────
  if (showReview && sessionId) {
    const unanswered = questions.filter(q => !answers[q.id]);
    
    return (
      <div className="max-w-3xl mx-auto p-4 sm:p-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">📋</span>
              {t("review.title")}
            </CardTitle>
            <CardDescription>{t("review.subtitle")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Progress Summary */}
            <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm text-muted-foreground">{t("review.answered")}</p>
                <p className="text-2xl font-bold text-green-600">{Object.keys(answers).length}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">{t("review.unanswered")}</p>
                <p className="text-2xl font-bold text-orange-600">{unanswered.length}</p>
              </div>
            </div>

            {/* Unanswered Warning */}
            {unanswered.length > 0 && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <p className="text-sm font-medium text-orange-800 mb-2">
                  ⚠️ {t("review.warning")}
                </p>
                <div className="flex flex-wrap gap-2">
                  {unanswered.slice(0, 10).map((q, idx) => (
                    <button
                      key={q.id}
                      onClick={() => {
                        const qIdx = questions.findIndex(question => question.id === q.id);
                        setCurrentIdx(qIdx);
                        setShowReview(false);
                      }}
                      className="px-3 py-1 rounded-md bg-white border border-orange-300 text-sm text-orange-700 hover:bg-orange-100 transition-colors"
                    >
                      Q{questions.indexOf(q) + 1}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowReview(false)}
                className="w-full sm:w-auto"
              >
                {t("review.backButton")}
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={submitMutation.isPending || Object.keys(answers).length === 0}
                className="w-full sm:flex-1 bg-brand-600 hover:bg-brand-700"
              >
                {submitMutation.isPending ? t("review.submitting") : t("submitButton")}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ── Quiz in progress ───────────────────────────────────────────────────────
  if (sessionId && currentQuestion) {
    const progress = ((currentIdx + 1) / questions.length) * 100;
    const isAnswered = !!answers[currentQuestion.id];

    return (
      <div className="max-w-3xl mx-auto p-4 sm:p-6 space-y-6">
        {/* Progress Header */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm font-medium text-gray-700">
                {t("question", { current: currentIdx + 1, total: questions.length })}
              </span>
              <span className="text-sm font-bold text-brand-600">{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="h-2" />
            <p className="text-xs text-muted-foreground mt-2 text-center">
              {t("progressHelp")}
            </p>
          </CardContent>
        </Card>

        {/* Question Card */}
        <Card className="border-2 border-brand-100">
          <CardHeader>
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-full bg-brand-100 text-brand-700 font-bold text-lg">
                {currentIdx + 1}
              </div>
              <div className="flex-1">
                <p className="text-lg font-medium text-gray-900 leading-relaxed">
                  {currentQuestion.text}
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {[1, 2, 3, 4, 5].map((v) => {
              const isSelected = answers[currentQuestion.id] === v;
              return (
                <button
                  key={v}
                  onClick={() => saveResponses(currentQuestion.id, v)}
                  className={`w-full text-left px-5 py-4 rounded-lg border-2 text-sm transition-all hover:border-brand-400 hover:bg-brand-50 hover:shadow-sm
                    ${isSelected 
                      ? "border-brand-500 bg-brand-50 shadow-md ring-2 ring-brand-200" 
                      : "border-gray-200 bg-white"
                    }`}
                  aria-pressed={isSelected}
                >
                  <div className="flex items-center gap-3">
                    <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm
                      ${isSelected ? "bg-brand-600 text-white" : "bg-gray-100 text-gray-600"}`}>
                      {v}
                    </div>
                    <span className={`flex-1 ${isSelected ? "font-semibold text-gray-900" : "text-gray-700"}`}>
                      {(t as (key: string) => string)(`scaleLabels.${v}`)}
                    </span>
                    {isSelected && (
                      <span className="text-brand-600">✓</span>
                    )}
                  </div>
                </button>
              );
            })}
          </CardContent>
        </Card>

        {/* Navigation Buttons */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                variant="outline"
                onClick={handlePrevious}
                disabled={currentIdx === 0}
                className="w-full sm:w-auto"
              >
                ← {t("previousButton")}
              </Button>
              <div className="flex-1" />
              <Button
                onClick={handleNext}
                disabled={!isAnswered}
                className="w-full sm:w-auto bg-brand-600 hover:bg-brand-700"
              >
                {currentIdx === questions.length - 1 ? t("reviewButton") : t("nextButton")} →
              </Button>
            </div>
            {!isAnswered && (
              <p className="text-xs text-orange-600 text-center mt-3">
                {t("answerRequired")}
              </p>
            )}
            
            {/* Submit Quiz Button - Always visible */}
            {Object.keys(answers).length >= questions.length * 0.5 && (
              <div className="mt-4 pt-4 border-t">
                <Button
                  onClick={() => setShowReview(true)}
                  variant="default"
                  className="w-full bg-green-600 hover:bg-green-700"
                >
                  ✅ {t("submitButton")} ({Object.keys(answers).length}/{questions.length} answered)
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  // ── Start screen ───────────────────────────────────────────────────────────
  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-brand-500 to-brand-600 text-white text-4xl mb-4 shadow-lg">
          🎯
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">
          {t("hero.title")}
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          {t("hero.description")}
        </p>
      </div>

      {/* Welcome Card */}
      <Card className="border-2 border-brand-200 bg-gradient-to-br from-brand-50 via-white to-white shadow-lg">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">{t("welcome.title")}</CardTitle>
          <CardDescription className="text-base">{t("welcome.subtitle")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* What You'll Get */}
          <div className="grid sm:grid-cols-3 gap-4">
            <div className="text-center p-4 rounded-lg bg-white border">
              <div className="text-3xl mb-2">⏱️</div>
              <p className="font-semibold text-gray-900 mb-1">{t("welcome.duration")}</p>
              <p className="text-sm text-muted-foreground">{t("welcome.durationDesc")}</p>
            </div>
            <div className="text-center p-4 rounded-lg bg-white border">
              <div className="text-3xl mb-2">📊</div>
              <p className="font-semibold text-gray-900 mb-1">{t("welcome.analysis")}</p>
              <p className="text-sm text-muted-foreground">{t("welcome.analysisDesc")}</p>
            </div>
            <div className="text-center p-4 rounded-lg bg-white border">
              <div className="text-3xl mb-2">🎓</div>
              <p className="font-semibold text-gray-900 mb-1">{t("welcome.recommendations")}</p>
              <p className="text-sm text-muted-foreground">{t("welcome.recommendationsDesc")}</p>
            </div>
          </div>

          {/* Existing Result Banner */}
          {existingResult && (
            <div className="bg-amber-50 border-2 border-amber-300 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">💡</span>
                <div className="flex-1">
                  <p className="font-semibold text-amber-900 mb-1">{t("resumeBanner")}</p>
                  <Button
                    variant="outline"
                    onClick={() => setResult(existingResult)}
                    className="mt-2 border-amber-300 text-amber-700 hover:bg-amber-100"
                    size="sm"
                  >
                    {t("viewPreviousButton")}
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Start Quiz Button */}
          <Button
            onClick={() => {
              console.log("Start Quiz button clicked");
              startMutation.mutate();
            }}
            disabled={startMutation.isPending}
            size="lg"
            className="w-full bg-brand-600 hover:bg-brand-700 text-lg py-6 shadow-lg hover:shadow-xl transition-all"
          >
            {startMutation.isPending ? t("loading") : `${t("startButton")} 🚀`}
          </Button>

          {/* Error Message */}
          {startMutation.isError && (
            <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4 text-sm">
              <div className="flex items-start gap-3">
                <span className="text-2xl">🔐</span>
                <div className="flex-1">
                  <p className="font-semibold text-red-900 mb-1">Sign In Required</p>
                  <p className="text-red-700 mb-3">You need to be signed in to take the quiz.</p>
                  <Button
                    onClick={() => window.location.href = "/en/sign-in?redirect=/en/aptitude"}
                    className="bg-red-600 hover:bg-red-700 text-white"
                    size="sm"
                  >
                    Go to Sign In →
                  </Button>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quiz Process Steps */}
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-xl">{t("process.title")}</CardTitle>
          <CardDescription>{t("process.subtitle")}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { icon: "🔍", title: t("process.step1"), desc: t("process.step1Desc") },
              { icon: "✍️", title: t("process.step2"), desc: t("process.step2Desc") },
              { icon: "📈", title: t("process.step3"), desc: t("process.step3Desc") },
              { icon: "🎯", title: t("process.step4"), desc: t("process.step4Desc") },
            ].map((step, idx) => (
              <div key={idx} className="relative">
                <div className="text-center p-4 rounded-lg border-2 border-gray-200 bg-white hover:border-brand-300 hover:bg-brand-50 transition-colors h-full">
                  <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-brand-100 text-brand-700 font-bold mb-3">
                    {idx + 1}
                  </div>
                  <div className="text-3xl mb-2">{step.icon}</div>
                  <h3 className="font-semibold text-gray-900 mb-2 text-sm">{step.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{step.desc}</p>
                </div>
                {idx < 3 && (
                  <div className="hidden lg:block absolute top-1/2 -right-2 transform -translate-y-1/2 text-brand-300 text-2xl z-10">
                    →
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Engineering Branches Overview */}
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-xl">{t("branches.title")}</CardTitle>
          <CardDescription>{t("branches.subtitle")}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { 
                key: "cse", 
                icon: "💻", 
                name: t("branches.cse.name"), 
                desc: t("branches.cse.desc"),
                color: "border-blue-200 bg-blue-50 hover:bg-blue-100"
              },
              { 
                key: "aids", 
                icon: "🤖", 
                name: t("branches.aids.name"), 
                desc: t("branches.aids.desc"),
                color: "border-purple-200 bg-purple-50 hover:bg-purple-100"
              },
              { 
                key: "ece", 
                icon: "📡", 
                name: t("branches.ece.name"), 
                desc: t("branches.ece.desc"),
                color: "border-green-200 bg-green-50 hover:bg-green-100"
              },
              { 
                key: "eee", 
                icon: "⚡", 
                name: t("branches.eee.name"), 
                desc: t("branches.eee.desc"),
                color: "border-yellow-200 bg-yellow-50 hover:bg-yellow-100"
              },
              { 
                key: "mech", 
                icon: "⚙️", 
                name: t("branches.mech.name"), 
                desc: t("branches.mech.desc"),
                color: "border-orange-200 bg-orange-50 hover:bg-orange-100"
              },
              { 
                key: "civil", 
                icon: "🏗️", 
                name: t("branches.civil.name"), 
                desc: t("branches.civil.desc"),
                color: "border-gray-200 bg-gray-50 hover:bg-gray-100"
              },
            ].map((branch) => (
              <div
                key={branch.key}
                className={`p-4 rounded-lg border-2 transition-all ${branch.color}`}
              >
                <div className="text-4xl mb-3">{branch.icon}</div>
                <h3 className="font-semibold text-gray-900 mb-2 text-sm">{branch.name}</h3>
                <p className="text-xs text-gray-600 leading-relaxed">{branch.desc}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* CTA Footer */}
      <Card className="border-2 border-brand-200 bg-brand-50">
        <CardContent className="pt-6 text-center space-y-4">
          <p className="text-lg font-medium text-gray-900">{t("cta.ready")}</p>
          <Button
            onClick={() => startMutation.mutate()}
            disabled={startMutation.isPending}
            size="lg"
            className="bg-brand-600 hover:bg-brand-700 px-8 py-6 text-lg shadow-lg"
          >
            {startMutation.isPending ? t("loading") : `${t("startButton")} 🎯`}
          </Button>
          <p className="text-sm text-muted-foreground">{t("cta.time")}</p>
        </CardContent>
      </Card>
    </div>
  );
}
