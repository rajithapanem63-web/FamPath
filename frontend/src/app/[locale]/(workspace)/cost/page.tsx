"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery, useMutation } from "@tanstack/react-query";
import { get, post } from "@/lib/api";
import { useWorkspaceStore } from "@/stores/workspaceStore";
import { cn } from "@/lib/utils";

interface FeeData {
  college_id: string;
  program_id: string;
  annual_fee_breakdown?: {
    tuition: number;
    hostel: number;
    transport: number;
    other: number;
  };
  total_annual_fee?: number;
  total_4yr_cost?: number;
  data_year?: number;
  data_source?: string;
  disclaimer?: string;
  error?: string;
}

interface ScholarshipItem {
  id: string;
  name: string;
  name_te?: string;
  name_hi?: string;
  provider: string;
  amount_per_year: number;
  covers_hostel: boolean;
  eligible_categories: string[];
  income_ceiling: number | null;
  application_url?: string;
  deadline_notes?: string;
  data_source?: string;
  data_year?: number;
  verification_status?: string;
  suitability_reasons?: string[];
}

interface LoanScenario {
  loan_amount: number;
  interest_rate_pct: number;
  tenure_months: number;
  monthly_emi: number;
  payback_months_at_30pct_salary: number | null;
}

interface RoiData {
  college_id: string;
  program_id: string;
  median_placement_lpa: number | null;
  placement_year: number | null;
  placement_source: string | null;
  loan_scenarios: LoanScenario[];
  disclaimer: string;
}

interface BudgetPlanResult {
  total_4yr_cost: number;
  total_scholarship_4yr: number;
  net_family_out_of_pocket: number;
  planned_budget_4yr: number;
  funding_gap: number;
  surplus: number;
  affordability_tier: string;
  affordability_color: "green" | "amber" | "red";
  breakdown_annual: {
    tuition: number;
    hostel: number;
    transport: number;
    other_college_fees: number;
    estimated_food_living: number;
  };
  assumptions: string[];
}

interface ShortlistItem {
  id: string;
  college_id: string;
  program_id: string;
  prediction_snapshot: { college_name?: string; branch_name?: string } | null;
}

export default function CostPage() {
  const t = useTranslations("cost");
  const { workspace } = useWorkspaceStore();

  const [activeTab, setActiveTab] = useState<"budget" | "scholarships" | "roi">("budget");

  // Fetch family shortlist to easily pick a college
  const { data: shortlist = [] } = useQuery({
    queryKey: ["shortlist", workspace?.id],
    queryFn: () => (workspace?.id ? get<ShortlistItem[]>(`/shortlist/${workspace.id}`) : []),
    enabled: !!workspace?.id,
  });

  const [selectedCollegeId, setSelectedCollegeId] = useState<string>("default");

  // Scholarship Finder Filters
  const [scholarshipCategory, setScholarshipCategory] = useState<string>("all");
  const [scholarshipIncome, setScholarshipIncome] = useState<string>("all");

  // Budget Planner State
  const [plannedBudget, setPlannedBudget] = useState<number>(300000);
  const [tuitionAnnual, setTuitionAnnual] = useState<number>(45000);
  const [hostelAnnual, setHostelAnnual] = useState<number>(40000);
  const [transportAnnual, setTransportAnnual] = useState<number>(10000);
  const [otherAnnual, setOtherAnnual] = useState<number>(5000);
  const [foodLivingAnnual, setFoodLivingAnnual] = useState<number>(25000);
  const [confirmedScholarship, setConfirmedScholarship] = useState<number>(0);

  // Fetch Scholarships
  const { data: scholarships = [], isLoading: isScholarshipsLoading } = useQuery({
    queryKey: ["scholarships", scholarshipCategory, scholarshipIncome],
    queryFn: () => {
      const params = new URLSearchParams();
      if (scholarshipCategory !== "all") params.append("category", scholarshipCategory);
      if (scholarshipIncome !== "all") params.append("income_range", scholarshipIncome);
      const queryStr = params.toString() ? `?${params.toString()}` : "";
      return get<ScholarshipItem[]>(`/cost/scholarships${queryStr}`);
    },
  });

  // Calculate Budget Plan
  const budgetPlanMutation = useMutation({
    mutationFn: () =>
      post<BudgetPlanResult>("/cost/budget-plan", {
        planned_budget_4yr: plannedBudget,
        annual_tuition: tuitionAnnual,
        annual_hostel: hostelAnnual,
        annual_transport: transportAnnual,
        annual_other: otherAnnual,
        annual_food_living: foodLivingAnnual,
        confirmed_scholarship_annual: confirmedScholarship,
      }),
  });

  // Loan calculator client-side state
  const [loanPrincipal, setLoanPrincipal] = useState<number>(200000);
  const [loanInterest, setLoanInterest] = useState<number>(8.5);
  const [loanTenure, setLoanTenure] = useState<number>(60);

  const calculateClientEmi = (p: number, r: number, n: number) => {
    if (p <= 0 || n <= 0) return 0;
    const monthlyRate = r / 12 / 100;
    if (monthlyRate === 0) return p / n;
    return (p * monthlyRate * Math.pow(1 + monthlyRate, n)) / (Math.pow(1 + monthlyRate, n) - 1);
  };

  const calculatedEmi = calculateClientEmi(loanPrincipal, loanInterest, loanTenure);

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <span className="text-3xl">💳</span>
          <h1 className="text-2xl font-bold text-gray-900">{t("title")}</h1>
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          4-Year cost planning, government & institutional scholarship matching, and family affordability analysis.
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-gray-200 gap-2">
        <button
          onClick={() => setActiveTab("budget")}
          className={cn(
            "px-4 py-2.5 text-sm font-semibold border-b-2 transition flex items-center gap-2",
            activeTab === "budget"
              ? "border-brand-600 text-brand-600"
              : "border-transparent text-gray-500 hover:text-gray-800"
          )}
        >
          <span>📊</span> Family Budget Planner
        </button>
        <button
          onClick={() => setActiveTab("scholarships")}
          className={cn(
            "px-4 py-2.5 text-sm font-semibold border-b-2 transition flex items-center gap-2",
            activeTab === "scholarships"
              ? "border-brand-600 text-brand-600"
              : "border-transparent text-gray-500 hover:text-gray-800"
          )}
        >
          <span>🎓</span> Scholarship Finder
        </button>
        <button
          onClick={() => setActiveTab("roi")}
          className={cn(
            "px-4 py-2.5 text-sm font-semibold border-b-2 transition flex items-center gap-2",
            activeTab === "roi"
              ? "border-brand-600 text-brand-600"
              : "border-transparent text-gray-500 hover:text-gray-800"
          )}
        >
          <span>📈</span> Loan & ROI Calculator
        </button>
      </div>

      {/* TAB 1: FAMILY BUDGET PLANNER (FEATURE 3) */}
      {activeTab === "budget" && (
        <div className="space-y-6 animate-in fade-in">
          <div className="bg-brand-50/50 border border-brand-200 rounded-2xl p-5 text-sm text-brand-950 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <p className="font-bold text-base">Plan Your Total 4-Year College Investment</p>
              <p className="text-xs text-brand-800 mt-0.5">
                Calculate the net funding gap between your family budget and estimated college expenses.
              </p>
            </div>
            {shortlist.length > 0 && (
              <div className="text-xs space-y-1">
                <span className="font-medium text-gray-700 block">Prefill fees from shortlist:</span>
                <select
                  value={selectedCollegeId}
                  onChange={(e) => {
                    const cid = e.target.value;
                    setSelectedCollegeId(cid);
                    if (cid !== "default") {
                      // Set standard average benchmark for selected college
                      setTuitionAnnual(50000);
                      setHostelAnnual(45000);
                    }
                  }}
                  className="rounded-lg border border-brand-300 bg-white px-2.5 py-1 text-xs"
                >
                  <option value="default">Custom / Benchmark College</option>
                  {shortlist.map((item) => (
                    <option key={item.id} value={item.college_id}>
                      {item.prediction_snapshot?.college_name ?? `College ${item.college_id.slice(0, 6)}`}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Input Column */}
            <div className="lg:col-span-1 bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-4">
              <h2 className="font-bold text-gray-900 text-base">Budget & Annual Costs</h2>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Family 4-Year Planned Budget (₹)
                </label>
                <input
                  type="number"
                  step="10000"
                  value={plannedBudget}
                  onChange={(e) => setPlannedBudget(parseFloat(e.target.value) || 0)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-semibold text-gray-900 focus:ring-2 focus:ring-brand-500"
                />
                <span className="text-[10px] text-muted-foreground">What family can contribute over 4 years</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Annual Tuition Fee (₹/year)
                </label>
                <input
                  type="number"
                  step="5000"
                  value={tuitionAnnual}
                  onChange={(e) => setTuitionAnnual(parseFloat(e.target.value) || 0)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Annual Hostel & Mess Fee (₹/year)
                </label>
                <input
                  type="number"
                  step="5000"
                  value={hostelAnnual}
                  onChange={(e) => setHostelAnnual(parseFloat(e.target.value) || 0)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Annual Transport Fee (₹/year)
                </label>
                <input
                  type="number"
                  step="2000"
                  value={transportAnnual}
                  onChange={(e) => setTransportAnnual(parseFloat(e.target.value) || 0)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Other Institution Fees (₹/year)
                </label>
                <input
                  type="number"
                  step="1000"
                  value={otherAnnual}
                  onChange={(e) => setOtherAnnual(parseFloat(e.target.value) || 0)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Estimated Food & Personal Living (₹/year)
                </label>
                <input
                  type="number"
                  step="2000"
                  value={foodLivingAnnual}
                  onChange={(e) => setFoodLivingAnnual(parseFloat(e.target.value) || 0)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                />
              </div>

              <div className="pt-2 border-t">
                <label className="block text-xs font-semibold text-green-700 mb-1">
                  Confirmed / Expected Scholarship (₹/year)
                </label>
                <input
                  type="number"
                  step="5000"
                  value={confirmedScholarship}
                  onChange={(e) => setConfirmedScholarship(parseFloat(e.target.value) || 0)}
                  className="w-full rounded-lg border border-green-300 bg-green-50/40 px-3 py-2 text-sm font-semibold text-green-800"
                />
                <span className="text-[10px] text-muted-foreground">Reduces annual out-of-pocket tuition</span>
              </div>

              <button
                onClick={() => budgetPlanMutation.mutate()}
                disabled={budgetPlanMutation.isPending}
                className="w-full rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold py-2.5 text-sm transition shadow-sm"
              >
                {budgetPlanMutation.isPending ? "Calculating…" : "Recalculate Budget Plan"}
              </button>
            </div>

            {/* Results Column */}
            <div className="lg:col-span-2 space-y-6">
              {(() => {
                const annualGross = tuitionAnnual + hostelAnnual + transportAnnual + otherAnnual + foodLivingAnnual;
                const total4YrCost = annualGross * 4;
                const totalScholarship4Yr = confirmedScholarship * 4;
                const netOutOfPocket = Math.max(0, total4YrCost - totalScholarship4Yr);
                const gap = Math.max(0, netOutOfPocket - plannedBudget);
                const surplus = Math.max(0, plannedBudget - netOutOfPocket);

                return (
                  <>
                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                      <div className="rounded-2xl border border-gray-200 bg-white p-5 space-y-1">
                        <span className="text-xs text-gray-500 font-medium">Total 4-Year Cost</span>
                        <p className="text-2xl font-black text-gray-900">
                          ₹{total4YrCost.toLocaleString("en-IN")}
                        </p>
                        <span className="text-[11px] text-gray-400 block">Gross 8 semesters</span>
                      </div>

                      <div className="rounded-2xl border border-gray-200 bg-white p-5 space-y-1">
                        <span className="text-xs text-gray-500 font-medium">Net Family Out-of-Pocket</span>
                        <p className="text-2xl font-black text-brand-700">
                          ₹{netOutOfPocket.toLocaleString("en-IN")}
                        </p>
                        <span className="text-[11px] text-green-600 block">
                          After ₹{totalScholarship4Yr.toLocaleString("en-IN")} scholarship
                        </span>
                      </div>

                      <div className={cn(
                        "rounded-2xl border p-5 space-y-1",
                        gap === 0
                          ? "bg-green-50 border-green-200"
                          : gap <= 150000
                          ? "bg-amber-50 border-amber-200"
                          : "bg-red-50 border-red-200"
                      )}>
                        <span className="text-xs font-medium block">
                          {gap === 0 ? "Budget Surplus" : "Estimated Funding Gap"}
                        </span>
                        <p className={cn(
                          "text-2xl font-black",
                          gap === 0 ? "text-green-700" : "text-red-700"
                        )}>
                          {gap === 0 ? `+₹${surplus.toLocaleString("en-IN")}` : `₹${gap.toLocaleString("en-IN")}`}
                        </p>
                        <span className="text-[11px] font-semibold block">
                          {gap === 0 ? "✓ 100% Within Budget" : "Requires Education Loan/Aid"}
                        </span>
                      </div>
                    </div>

                    {/* Affordability Tier Badge */}
                    <div className={cn(
                      "rounded-xl border p-4 text-sm font-semibold flex items-center justify-between",
                      gap === 0
                        ? "bg-green-50/70 border-green-200 text-green-900"
                        : gap <= 150000
                        ? "bg-amber-50/70 border-amber-200 text-amber-900"
                        : "bg-red-50/70 border-red-200 text-red-900"
                    )}>
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{gap === 0 ? "🟢" : gap <= 150000 ? "🟡" : "🔴"}</span>
                        <span>Affordability Rating: {gap === 0 ? "Fully Affordable" : gap <= 150000 ? "Moderate Funding Gap" : "High Funding Gap"}</span>
                      </div>
                      <span className="text-xs font-normal">
                        {gap === 0
                          ? "Your planned family budget covers all 4 years."
                          : `Funding shortfall of ₹${gap.toLocaleString("en-IN")} needed across 4 years.`}
                      </span>
                    </div>

                    {/* 4-Year Breakdown Table */}
                    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
                      <div className="px-5 py-3.5 bg-gray-50 border-b">
                        <h3 className="font-bold text-sm text-gray-900">Annual vs 4-Year Expense Breakdown</h3>
                      </div>
                      <div className="divide-y text-xs">
                        <div className="flex justify-between p-3">
                          <span className="text-gray-600">College Tuition Fee</span>
                          <span className="font-semibold">₹{tuitionAnnual.toLocaleString("en-IN")} / yr (₹{(tuitionAnnual * 4).toLocaleString("en-IN")} 4yr)</span>
                        </div>
                        <div className="flex justify-between p-3">
                          <span className="text-gray-600">Hostel & Mess Boarding</span>
                          <span className="font-semibold">₹{hostelAnnual.toLocaleString("en-IN")} / yr (₹{(hostelAnnual * 4).toLocaleString("en-IN")} 4yr)</span>
                        </div>
                        <div className="flex justify-between p-3">
                          <span className="text-gray-600">Commute & Transportation</span>
                          <span className="font-semibold">₹{transportAnnual.toLocaleString("en-IN")} / yr (₹{(transportAnnual * 4).toLocaleString("en-IN")} 4yr)</span>
                        </div>
                        <div className="flex justify-between p-3">
                          <span className="text-gray-600">Other Academic Fees (Lab, Library)</span>
                          <span className="font-semibold">₹{otherAnnual.toLocaleString("en-IN")} / yr (₹{(otherAnnual * 4).toLocaleString("en-IN")} 4yr)</span>
                        </div>
                        <div className="flex justify-between p-3">
                          <span className="text-gray-600">Estimated Books & Personal Living</span>
                          <span className="font-semibold">₹{foodLivingAnnual.toLocaleString("en-IN")} / yr (₹{(foodLivingAnnual * 4).toLocaleString("en-IN")} 4yr)</span>
                        </div>
                        <div className="flex justify-between p-3 bg-green-50/50 text-green-900 font-semibold">
                          <span>Less Confirmed Scholarship Deductions</span>
                          <span>−₹{confirmedScholarship.toLocaleString("en-IN")} / yr (−₹{(confirmedScholarship * 4).toLocaleString("en-IN")} 4yr)</span>
                        </div>
                      </div>
                    </div>

                    {/* Planning Assumptions */}
                    <div className="bg-white rounded-2xl border border-gray-200 p-5 space-y-2 text-xs">
                      <p className="font-bold text-gray-900">📌 Calculation Assumptions</p>
                      <ul className="list-disc list-inside space-y-1 text-gray-600">
                        <li>Standard 4-year undergraduate engineering curriculum (8 terms).</li>
                        <li>Assumes institutional fees remain consistent without mid-cycle escalation.</li>
                        <li>Scholarship renewal requires maintaining qualifying academic merit and attendance.</li>
                        <li>No guarantee of scholarship sanction, bank loan approval, or future salary returns.</li>
                      </ul>
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: SCHOLARSHIP FINDER (FEATURE 1) */}
      {activeTab === "scholarships" && (
        <div className="space-y-6 animate-in fade-in">
          {/* Filters Bar */}
          <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm flex flex-wrap items-center gap-4 text-sm">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Reservation Category</label>
              <select
                value={scholarshipCategory}
                onChange={(e) => setScholarshipCategory(e.target.value)}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs bg-white focus:ring-2 focus:ring-brand-500"
              >
                <option value="all">All Categories</option>
                <option value="OC">Open Competition (OC / General)</option>
                <option value="BC_A">BC-A</option>
                <option value="BC_B">BC-B</option>
                <option value="BC_C">BC-C</option>
                <option value="BC_D">BC-D</option>
                <option value="BC_E">BC-E</option>
                <option value="SC">Scheduled Caste (SC)</option>
                <option value="ST">Scheduled Tribe (ST)</option>
                <option value="EWS">Economically Weaker Section (EWS)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Family Income Range</label>
              <select
                value={scholarshipIncome}
                onChange={(e) => setScholarshipIncome(e.target.value)}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs bg-white focus:ring-2 focus:ring-brand-500"
              >
                <option value="all">Any Income</option>
                <option value="low">Under ₹2.0 Lakhs / year</option>
                <option value="medium">₹2.0 Lakhs – ₹8.0 Lakhs / year</option>
                <option value="high">Above ₹8.0 Lakhs / year</option>
              </select>
            </div>

            <div className="ml-auto text-xs text-muted-foreground self-end pb-1">
              Found {scholarships.length} scholarships matching criteria
            </div>
          </div>

          {/* Scholarship List */}
          {isScholarshipsLoading ? (
            <div className="py-20 text-center space-y-2">
              <div className="animate-spin text-3xl inline-block">🔄</div>
              <p className="text-xs text-muted-foreground font-medium">Matching eligible scholarships…</p>
            </div>
          ) : scholarships.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-gray-300 p-12 text-center text-muted-foreground">
              <p className="text-4xl mb-2">🔍</p>
              <p className="font-semibold">{t("noScholarships")}</p>
              <p className="text-xs mt-1">Try broadening your category or income filter.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {scholarships.map((s) => (
                <div
                  key={s.id}
                  className="rounded-2xl border border-gray-200 bg-white p-5 space-y-4 hover:border-brand-300 shadow-sm transition flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h2 className="font-bold text-gray-900 text-sm leading-snug">{s.name}</h2>
                        <p className="text-xs text-brand-700 font-medium mt-0.5">{s.provider}</p>
                      </div>
                      <span className={cn(
                        "rounded-full px-2 py-0.5 text-[10px] font-bold border flex-shrink-0",
                        s.verification_status === "verified"
                          ? "bg-green-50 text-green-700 border-green-200"
                          : "bg-gray-100 text-gray-600 border-gray-200"
                      )}>
                        {s.verification_status === "verified" ? "✓ Verified Scheme" : "Sample Data"}
                      </span>
                    </div>

                    {/* Financial Value Pill */}
                    <div className="flex items-center gap-3 text-xs bg-gray-50 p-2.5 rounded-xl border border-gray-100">
                      <div>
                        <span className="text-[10px] text-gray-500 block">Grant Amount</span>
                        <span className="font-bold text-gray-900">
                          {s.amount_per_year > 0 ? `₹${s.amount_per_year.toLocaleString("en-IN")} / year` : "Full Tuition Reimbursement"}
                        </span>
                      </div>
                      <div className="border-l pl-3">
                        <span className="text-[10px] text-gray-500 block">Hostel Aid</span>
                        <span className="font-semibold text-gray-800">
                          {s.covers_hostel ? "✓ Included" : "Tuition Only"}
                        </span>
                      </div>
                    </div>

                    {/* Eligibility & Suitability Reasons */}
                    {s.suitability_reasons && s.suitability_reasons.length > 0 && (
                      <div className="space-y-1 pt-1">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-brand-800">Why Suitable:</span>
                        <ul className="text-xs text-gray-700 space-y-0.5">
                          {s.suitability_reasons.map((r, idx) => (
                            <li key={idx} className="flex items-center gap-1.5">
                              <span className="text-green-600">✓</span> {r}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Deadline Notes */}
                    {s.deadline_notes && (
                      <div className="text-xs bg-amber-50/60 border border-amber-200/80 rounded-lg p-2 text-amber-900">
                        <span className="font-semibold">Official Timeline:</span> {s.deadline_notes}
                      </div>
                    )}
                  </div>

                  {/* Actions & Official Link */}
                  <div className="pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
                    {s.application_url ? (
                      <a
                        href={s.application_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-medium text-brand-600 hover:underline flex items-center gap-1"
                      >
                        Official Portal ↗
                      </a>
                    ) : (
                      <span className="text-gray-400 italic">Verify via state portal</span>
                    )}

                    <button
                      onClick={() => {
                        setConfirmedScholarship(s.amount_per_year || 45000);
                        setActiveTab("budget");
                      }}
                      className="rounded-lg bg-brand-50 hover:bg-brand-100 text-brand-700 font-semibold px-3 py-1.5 border border-brand-200 transition"
                    >
                      Use in Budget Plan →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Disclaimer */}
          <div className="rounded-xl bg-amber-50 border border-amber-200 p-4 text-xs text-amber-900 space-y-1">
            <p className="font-bold">⚠️ Scholarship Verification Notice</p>
            <p>
              Scholarship schemes, eligibility thresholds, and deadlines are maintained from verified public gazettes and government portals.
              FamPath does not invent scholarships or guarantee award sanctions. Application must be submitted directly through official portals.
            </p>
          </div>
        </div>
      )}

      {/* TAB 3: LOAN & ROI CALCULATOR */}
      {activeTab === "roi" && (
        <div className="space-y-6 animate-in fade-in">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Interactive Loan Simulator */}
            <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-5">
              <h2 className="font-bold text-gray-900 text-base">{t("loanCalculator")}</h2>

              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span>{t("loanAmount")}</span>
                  <span className="text-brand-600 font-bold">₹{loanPrincipal.toLocaleString("en-IN")}</span>
                </div>
                <input
                  type="range"
                  min="50000"
                  max="1500000"
                  step="25000"
                  value={loanPrincipal}
                  onChange={(e) => setLoanPrincipal(parseInt(e.target.value))}
                  className="w-full accent-brand-600"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span>{t("interestRate")}</span>
                  <span className="text-brand-600 font-bold">{loanInterest}%</span>
                </div>
                <input
                  type="range"
                  min="6.0"
                  max="14.0"
                  step="0.25"
                  value={loanInterest}
                  onChange={(e) => setLoanInterest(parseFloat(e.target.value))}
                  className="w-full accent-brand-600"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span>{t("tenure")}</span>
                  <span className="text-brand-600 font-bold">{loanTenure} months ({loanTenure / 12} yrs)</span>
                </div>
                <input
                  type="range"
                  min="12"
                  max="120"
                  step="12"
                  value={loanTenure}
                  onChange={(e) => setLoanTenure(parseInt(e.target.value))}
                  className="w-full accent-brand-600"
                />
              </div>

              <div className="rounded-xl bg-brand-50 border border-brand-200 p-4 space-y-1">
                <span className="text-xs text-brand-900 font-medium">{t("monthlyEmi")}</span>
                <p className="text-3xl font-black text-brand-700">₹{Math.round(calculatedEmi).toLocaleString("en-IN")}</p>
                <p className="text-[11px] text-brand-800">
                  Total Repayment: ₹{Math.round(calculatedEmi * loanTenure).toLocaleString("en-IN")} (Interest: ₹{Math.round(calculatedEmi * loanTenure - loanPrincipal).toLocaleString("en-IN")})
                </p>
              </div>
            </div>

            {/* ROI & Payback Context */}
            <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-4">
              <h2 className="font-bold text-gray-900 text-base">{t("roiTitle")}</h2>
              <p className="text-xs text-muted-foreground">
                Understand repayment feasibility relative to starting engineering salaries.
              </p>

              <div className="space-y-3">
                <div className="rounded-xl border p-4 bg-gray-50 space-y-1">
                  <span className="text-xs text-gray-500">Benchmark Starting Salary (Median LPA)</span>
                  <p className="text-xl font-bold text-gray-900">₹6.5 LPA (₹54,166 / month)</p>
                  <span className="text-[10px] text-muted-foreground">Regional engineering campus average</span>
                </div>

                <div className="rounded-xl border p-4 bg-green-50/70 border-green-200 space-y-1">
                  <span className="text-xs text-green-800 font-medium">Estimated Payback Period</span>
                  <p className="text-xl font-bold text-green-900">
                    {Math.round(loanPrincipal / ((650000 / 12) * 0.3))} Months
                  </p>
                  <p className="text-[11px] text-green-700">
                    Assuming standard 30% of monthly net compensation allocated toward education loan amortisation.
                  </p>
                </div>
              </div>

              <div className="rounded-xl bg-gray-50 border p-4 text-xs text-gray-600 space-y-1">
                <p className="font-semibold text-gray-800">📌 Decision Guidance</p>
                <p>
                  A healthy education loan has an EMI that stays below 25-30% of the projected starting salary.
                  Loan approvals depend strictly on financial underwriting, CIBIL score, and co-applicant eligibility.
                </p>
              </div>
            </div>
          </div>

          {/* Legal Disclaimer */}
          <div className="rounded-xl bg-amber-50 border border-amber-200 p-4 text-xs text-amber-900">
            ⚠️ {t("disclaimer")} FamPath does not guarantee bank loan approvals, interest subsidies, or future compensation packages.
          </div>
        </div>
      )}
    </div>
  );
}
