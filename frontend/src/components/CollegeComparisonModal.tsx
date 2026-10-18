"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { post } from "@/lib/api";
import { cn } from "@/lib/utils";

export interface CompareTarget {
  college_id: string;
  program_id?: string;
  college_name: string;
  branch_name?: string;
}

interface CollegeComparisonItem {
  college_id: string;
  college_code: string;
  name: string;
  college_type: string | null;
  state: string | null;
  district: string | null;
  city: string | null;
  affiliation: string | null;
  naac_grade: string | null;
  established_year: number | null;
  website: string | null;
  program_id: string | null;
  branch_code: string | null;
  branch_name: string | null;
  intake_seats: number | null;
  annual_tuition: number | null;
  annual_hostel: number | null;
  annual_transport: number | null;
  annual_total: number | null;
  estimated_4yr_cost: number | null;
  fee_data_year: number | null;
  fee_source: string | null;
  placed_percent: number | null;
  median_package_lpa: number | null;
  avg_package_lpa: number | null;
  highest_package_lpa: number | null;
  top_recruiters: string[];
  placement_year: number | null;
  placement_source: string | null;
  missing_fields: string[];
}

interface CompareResponse {
  colleges: CollegeComparisonItem[];
  insights: string[];
  disclaimer: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  availableColleges: CompareTarget[];
  initialSelectedIds?: string[];
}

export default function CollegeComparisonModal({
  isOpen,
  onClose,
  availableColleges,
  initialSelectedIds = [],
}: Props) {
  const [selectedIds, setSelectedIds] = useState<string[]>(() => {
    if (initialSelectedIds.length >= 2) return initialSelectedIds.slice(0, 4);
    return availableColleges.slice(0, 2).map((c) => c.college_id);
  });

  const toggleCollege = (id: string) => {
    if (selectedIds.includes(id)) {
      if (selectedIds.length > 2) {
        setSelectedIds(selectedIds.filter((item) => item !== id));
      }
    } else {
      if (selectedIds.length < 4) {
        setSelectedIds([...selectedIds, id]);
      }
    }
  };

  const payloadItems = selectedIds.map((id) => {
    const match = availableColleges.find((c) => c.college_id === id);
    return {
      college_id: id,
      program_id: match?.program_id,
    };
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ["college-compare", selectedIds],
    queryFn: () =>
      post<CompareResponse>("/colleges/compare", { items: payloadItems }),
    enabled: isOpen && selectedIds.length >= 2,
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-in fade-in">
      <div className="relative max-h-[90vh] w-full max-w-6xl overflow-hidden rounded-2xl bg-white shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4 bg-gray-50">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">⚖️</span>
              <h2 className="text-xl font-bold text-gray-900">Side-by-Side College Comparison</h2>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Compare 2 to 4 engineering options on fees, placements, branch details, and facilities.
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-200 hover:text-gray-700 transition"
            aria-label="Close comparison"
          >
            ✕
          </button>
        </div>

        {/* Selection Bar */}
        <div className="border-b px-6 py-3 bg-brand-50/40 flex flex-wrap items-center gap-2 text-xs">
          <span className="font-semibold text-gray-700">Comparing ({selectedIds.length}/4):</span>
          {availableColleges.map((c) => {
            const isSelected = selectedIds.includes(c.college_id);
            return (
              <button
                key={c.college_id}
                onClick={() => toggleCollege(c.college_id)}
                className={cn(
                  "rounded-full px-3 py-1 font-medium border transition-colors",
                  isSelected
                    ? "bg-brand-600 text-white border-brand-600 shadow-sm"
                    : "bg-white text-gray-700 border-gray-300 hover:border-brand-400"
                )}
              >
                {isSelected ? "✓ " : "+ "}
                {c.college_name.slice(0, 24)}
                {c.branch_name ? ` (${c.branch_name.slice(0, 10)})` : ""}
              </button>
            );
          })}
        </div>

        {/* Content Body */}
        <div className="overflow-y-auto p-6 space-y-6 flex-1">
          {isLoading ? (
            <div className="py-20 text-center space-y-3">
              <div className="animate-spin text-4xl inline-block">🔄</div>
              <p className="text-muted-foreground text-sm font-medium">Fetching verified comparison metrics…</p>
            </div>
          ) : error || !data ? (
            <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center text-sm text-red-700">
              Unable to load comparison data. Please ensure at least 2 colleges are selected.
            </div>
          ) : (
            <>
              {/* Rule-based Insights */}
              {data.insights.length > 0 && (
                <div className="rounded-xl border border-brand-200 bg-brand-50/50 p-4 space-y-2">
                  <p className="text-xs font-bold text-brand-900 uppercase tracking-wider flex items-center gap-1.5">
                    <span>💡</span> Key Decision Takeaways
                  </p>
                  <ul className="list-disc list-inside text-sm text-brand-950 space-y-1">
                    {data.insights.map((insight, idx) => (
                      <li key={idx} className="leading-relaxed">{insight}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Comparison Table */}
              <div className="overflow-x-auto rounded-xl border border-gray-200 shadow-sm">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="bg-gray-100 text-gray-900 border-b">
                      <th className="p-3 font-semibold w-1/5 min-w-[160px] bg-gray-100 sticky left-0 z-10">
                        Feature / Metric
                      </th>
                      {data.colleges.map((c) => (
                        <th key={c.college_id} className="p-3 font-bold min-w-[220px] border-l">
                          <div>
                            <p className="text-base text-gray-900">{c.name}</p>
                            <p className="text-xs text-brand-600 font-normal">
                              {c.branch_name ?? c.branch_code ?? "Engineering"}
                            </p>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {/* Basic Info */}
                    <tr className="bg-gray-50/50">
                      <td colSpan={data.colleges.length + 1} className="p-2 text-xs font-bold text-gray-500 uppercase tracking-wider">
                        Institution & Campus
                      </td>
                    </tr>
                    <tr>
                      <td className="p-3 font-medium text-gray-700 bg-gray-50/30 sticky left-0">Type & Governance</td>
                      {data.colleges.map((c) => (
                        <td key={c.college_id} className="p-3 border-l capitalize">
                          {c.college_type ? c.college_type.replace(/_/g, " ") : "Not reported"}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-3 font-medium text-gray-700 bg-gray-50/30 sticky left-0">Location</td>
                      {data.colleges.map((c) => (
                        <td key={c.college_id} className="p-3 border-l">
                          {[c.city, c.district, c.state].filter(Boolean).join(", ") || "Not reported"}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-3 font-medium text-gray-700 bg-gray-50/30 sticky left-0">NAAC Grade</td>
                      {data.colleges.map((c) => (
                        <td key={c.college_id} className="p-3 border-l">
                          {c.naac_grade ? (
                            <span className="inline-block rounded-md bg-blue-50 px-2 py-0.5 text-xs font-bold text-blue-700 border border-blue-200">
                              Grade {c.naac_grade}
                            </span>
                          ) : (
                            <span className="text-xs text-gray-400 italic">Not available</span>
                          )}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-3 font-medium text-gray-700 bg-gray-50/30 sticky left-0">Affiliation & Est.</td>
                      {data.colleges.map((c) => (
                        <td key={c.college_id} className="p-3 border-l text-xs">
                          {c.affiliation ?? "Autonomous / University"} {c.established_year ? `(Est. ${c.established_year})` : ""}
                        </td>
                      ))}
                    </tr>

                    {/* Fees & Education Cost */}
                    <tr className="bg-gray-50/50">
                      <td colSpan={data.colleges.length + 1} className="p-2 text-xs font-bold text-gray-500 uppercase tracking-wider">
                        Cost & Financials
                      </td>
                    </tr>
                    <tr>
                      <td className="p-3 font-medium text-gray-700 bg-gray-50/30 sticky left-0">Annual Tuition Fee</td>
                      {data.colleges.map((c) => (
                        <td key={c.college_id} className="p-3 border-l font-semibold text-gray-900">
                          {c.annual_tuition !== null ? `₹${c.annual_tuition.toLocaleString("en-IN")}` : "Not reported"}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-3 font-medium text-gray-700 bg-gray-50/30 sticky left-0">Hostel & Living Fee (Est.)</td>
                      {data.colleges.map((c) => (
                        <td key={c.college_id} className="p-3 border-l text-gray-700">
                          {c.annual_hostel !== null ? `₹${c.annual_hostel.toLocaleString("en-IN")} / yr` : "Campus hostel fee unlisted"}
                        </td>
                      ))}
                    </tr>
                    <tr className="bg-brand-50/20">
                      <td className="p-3 font-bold text-brand-900 bg-brand-50/40 sticky left-0">Est. Total 4-Year Cost</td>
                      {data.colleges.map((c) => (
                        <td key={c.college_id} className="p-3 border-l font-bold text-brand-700 text-base">
                          {c.estimated_4yr_cost !== null ? `₹${c.estimated_4yr_cost.toLocaleString("en-IN")}` : "Incomplete fee data"}
                          {c.fee_data_year && (
                            <p className="text-[11px] text-muted-foreground font-normal">
                              Source year: {c.fee_data_year}
                            </p>
                          )}
                        </td>
                      ))}
                    </tr>

                    {/* Placement Statistics */}
                    <tr className="bg-gray-50/50">
                      <td colSpan={data.colleges.length + 1} className="p-2 text-xs font-bold text-gray-500 uppercase tracking-wider">
                        Placement Track Record
                      </td>
                    </tr>
                    <tr>
                      <td className="p-3 font-medium text-gray-700 bg-gray-50/30 sticky left-0">Placed Percentage</td>
                      {data.colleges.map((c) => (
                        <td key={c.college_id} className="p-3 border-l">
                          {c.placed_percent !== null ? (
                            <span className="font-semibold text-green-700">{c.placed_percent}%</span>
                          ) : (
                            <span className="text-gray-400 italic">Not reported</span>
                          )}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-3 font-medium text-gray-700 bg-gray-50/30 sticky left-0">Median Package</td>
                      {data.colleges.map((c) => (
                        <td key={c.college_id} className="p-3 border-l font-semibold text-gray-900">
                          {c.median_package_lpa !== null ? `₹${c.median_package_lpa.toFixed(1)} LPA` : "Not reported"}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-3 font-medium text-gray-700 bg-gray-50/30 sticky left-0">Highest Package</td>
                      {data.colleges.map((c) => (
                        <td key={c.college_id} className="p-3 border-l text-gray-700">
                          {c.highest_package_lpa !== null ? `₹${c.highest_package_lpa.toFixed(1)} LPA` : "Not reported"}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-3 font-medium text-gray-700 bg-gray-50/30 sticky left-0">Top Recruiters</td>
                      {data.colleges.map((c) => (
                        <td key={c.college_id} className="p-3 border-l text-xs">
                          {c.top_recruiters && c.top_recruiters.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {c.top_recruiters.slice(0, 4).map((r, i) => (
                                <span key={i} className="rounded bg-gray-100 px-1.5 py-0.5 text-gray-700">
                                  {r}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="text-gray-400 italic">Not published</span>
                          )}
                          {c.placement_year && (
                            <p className="text-[10px] text-muted-foreground mt-1">Reporting yr: {c.placement_year}</p>
                          )}
                        </td>
                      ))}
                    </tr>

                    {/* Data Integrity & Missing Info */}
                    <tr className="bg-gray-50/50">
                      <td colSpan={data.colleges.length + 1} className="p-2 text-xs font-bold text-gray-500 uppercase tracking-wider">
                        Information Completeness
                      </td>
                    </tr>
                    <tr>
                      <td className="p-3 font-medium text-gray-700 bg-gray-50/30 sticky left-0">Data Gaps Identified</td>
                      {data.colleges.map((c) => (
                        <td key={c.college_id} className="p-3 border-l text-xs">
                          {c.missing_fields.length === 0 ? (
                            <span className="text-green-700 font-medium">✓ Complete records</span>
                          ) : (
                            <ul className="list-disc list-inside text-amber-700 space-y-0.5">
                              {c.missing_fields.map((mf, i) => (
                                <li key={i}>{mf}</li>
                              ))}
                            </ul>
                          )}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Disclaimer */}
              <p className="disclaimer-badge text-xs bg-amber-50/80 border border-amber-200 text-amber-900 p-3 rounded-lg">
                ⚠️ {data.disclaimer}
              </p>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="border-t px-6 py-3 bg-gray-50 flex items-center justify-between">
          <span className="text-xs text-muted-foreground">FamPath AI Decision Support</span>
          <button
            onClick={onClose}
            className="rounded-lg bg-gray-900 text-white px-5 py-2 text-sm font-medium hover:bg-gray-800 transition"
          >
            Close Comparison
          </button>
        </div>
      </div>
    </div>
  );
}
