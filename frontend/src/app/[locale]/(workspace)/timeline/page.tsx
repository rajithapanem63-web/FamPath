"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { get, post, put, del } from "@/lib/api";
import { useWorkspaceStore } from "@/stores/workspaceStore";
import { formatDaysLeft, cn } from "@/lib/utils";

interface TimelineItem {
  id: string;
  event_name: string;
  exam_type: string | null;
  event_date: string | null;
  round_number: number | null;
  is_completed: boolean;
  source_type: "official" | "user_entered" | string;
  source_citation: string;
  notes?: string | null;
  can_delete: boolean;
}

interface ChecklistItem {
  id: string;
  document_name: string;
  is_mandatory: boolean;
  is_completed: boolean;
}

export default function TimelinePage() {
  const t = useTranslations("timeline");
  const { workspace } = useWorkspaceStore();
  const qc = useQueryClient();

  const [activeTab, setActiveTab] = useState<"all" | "official" | "tasks" | "documents">("all");
  const [showAddModal, setShowAddModal] = useState(false);
  const [taskForm, setTaskForm] = useState({
    title: "",
    due_date: "",
    description: "",
    source_citation: "",
  });
  const [formError, setFormError] = useState<string | null>(null);

  // Queries
  const { data: timelineItems = [], isLoading: isLoadingTimeline } = useQuery({
    queryKey: ["timeline", workspace?.id],
    queryFn: () => get<TimelineItem[]>(`/timeline/${workspace?.id}`),
    enabled: !!workspace?.id,
  });

  const { data: checklist = [], isLoading: isLoadingChecklist } = useQuery({
    queryKey: ["checklist", workspace?.id],
    queryFn: () => get<ChecklistItem[]>(`/checklist/${workspace?.id}`),
    enabled: !!workspace?.id,
  });

  // Mutations
  const toggleChecklistMutation = useMutation({
    mutationFn: (itemId: string) =>
      put<{ is_completed: boolean }>(`/checklist/${workspace?.id}/${itemId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["checklist", workspace?.id] }),
  });

  const toggleTaskMutation = useMutation({
    mutationFn: (taskId: string) =>
      put<{ is_completed: boolean }>(`/timeline/${workspace?.id}/tasks/${taskId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["timeline", workspace?.id] }),
  });

  const deleteTaskMutation = useMutation({
    mutationFn: (taskId: string) =>
      del<{ message: string }>(`/timeline/${workspace?.id}/tasks/${taskId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["timeline", workspace?.id] }),
  });

  const createTaskMutation = useMutation({
    mutationFn: (newTask: typeof taskForm) =>
      post<{ id: string; title: string }>(`/timeline/${workspace?.id}/tasks`, newTask),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["timeline", workspace?.id] });
      setShowAddModal(false);
      setTaskForm({ title: "", due_date: "", description: "", source_citation: "" });
      setFormError(null);
    },
    onError: (err: any) => {
      setFormError(err?.response?.data?.detail || "Failed to create task. Please try again.");
    },
  });

  if (!workspace) {
    return (
      <div className="max-w-4xl mx-auto p-8 text-center bg-white rounded-2xl border border-gray-100 shadow-sm mt-8">
        <p className="text-gray-500 font-medium">Please select or create a workspace to view your admission timeline.</p>
      </div>
    );
  }

  // Derived metrics
  const officialEvents = timelineItems.filter((i) => i.source_type === "official");
  const userTasks = timelineItems.filter((i) => i.source_type !== "official");
  const pendingTasks = userTasks.filter((t) => !t.is_completed);

  const completedDocs = checklist.filter((i) => i.is_completed).length;
  const totalDocs = checklist.length;
  const docPct = totalDocs > 0 ? Math.round((completedDocs / totalDocs) * 100) : 0;

  // Filter items based on activeTab
  const filteredTimeline = timelineItems.filter((item) => {
    if (activeTab === "official") return item.source_type === "official";
    if (activeTab === "tasks") return item.source_type !== "official";
    return true;
  });

  const handleCreateTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskForm.title.trim()) {
      setFormError("Task title is required.");
      return;
    }
    createTaskMutation.mutate(taskForm);
  };

  const applyPreset = (presetTitle: string, presetCitation: string) => {
    setTaskForm((prev) => ({
      ...prev,
      title: presetTitle,
      source_citation: presetCitation,
    }));
  };

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gray-100 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">
            {t("title") || "Smart Admission Timeline & Reminders"}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Track verified counselling authority schedules, document submission dates, and custom family reminders.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-sm font-semibold transition-all shadow-sm hover:shadow-md cursor-pointer"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
          </svg>
          Add Custom Reminder
        </button>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Official Milestones</p>
          <p className="text-2xl font-bold text-blue-700 mt-1">{officialEvents.length}</p>
          <p className="text-xs text-gray-500 mt-0.5">Authority verified</p>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Family Tasks</p>
          <p className="text-2xl font-bold text-brand-600 mt-1">{userTasks.length}</p>
          <p className="text-xs text-gray-500 mt-0.5">{pendingTasks.length} pending</p>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Documents Ready</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">
            {completedDocs}/{totalDocs}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">{docPct}% verified</p>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Workspace State</p>
          <p className="text-2xl font-bold text-purple-700 mt-1">Active</p>
          <p className="text-xs text-gray-500 mt-0.5">Family synced</p>
        </div>
      </div>

      {/* Navigation Filter Tabs */}
      <div className="flex border-b border-gray-200 gap-2 sm:gap-4 overflow-x-auto">
        <button
          onClick={() => setActiveTab("all")}
          className={cn(
            "pb-3 text-sm font-semibold transition-colors border-b-2 cursor-pointer whitespace-nowrap px-1",
            activeTab === "all"
              ? "border-brand-600 text-brand-700"
              : "border-transparent text-gray-500 hover:text-gray-900"
          )}
        >
          All Timeline Events ({timelineItems.length})
        </button>
        <button
          onClick={() => setActiveTab("official")}
          className={cn(
            "pb-3 text-sm font-semibold transition-colors border-b-2 cursor-pointer whitespace-nowrap px-1",
            activeTab === "official"
              ? "border-blue-600 text-blue-700"
              : "border-transparent text-gray-500 hover:text-gray-900"
          )}
        >
          Official Dates ({officialEvents.length})
        </button>
        <button
          onClick={() => setActiveTab("tasks")}
          className={cn(
            "pb-3 text-sm font-semibold transition-colors border-b-2 cursor-pointer whitespace-nowrap px-1",
            activeTab === "tasks"
              ? "border-brand-600 text-brand-700"
              : "border-transparent text-gray-500 hover:text-gray-900"
          )}
        >
          Family Tasks ({userTasks.length})
        </button>
        <button
          onClick={() => setActiveTab("documents")}
          className={cn(
            "pb-3 text-sm font-semibold transition-colors border-b-2 cursor-pointer whitespace-nowrap px-1",
            activeTab === "documents"
              ? "border-emerald-600 text-emerald-700"
              : "border-transparent text-gray-500 hover:text-gray-900"
          )}
        >
          Document Checklist ({completedDocs}/{totalDocs})
        </button>
      </div>

      {/* Tab: Timeline / Reminders */}
      {activeTab !== "documents" && (
        <div className="space-y-4">
          {isLoadingTimeline ? (
            <div className="p-8 text-center text-gray-400">Loading timeline dates...</div>
          ) : filteredTimeline.length === 0 ? (
            <div className="rounded-2xl border-2 border-dashed border-gray-200 p-12 text-center bg-gray-50">
              <p className="text-gray-600 font-medium">{t("noEvents") || "No upcoming events found."}</p>
              <button
                onClick={() => setShowAddModal(true)}
                className="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-600 hover:text-brand-700 cursor-pointer"
              >
                + Add your first family admission reminder
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredTimeline.map((item) => {
                const daysLeft = item.event_date ? formatDaysLeft(item.event_date) : "TBD";
                const isPast = daysLeft.includes("ago");
                const isToday = daysLeft === "Today";
                const isOfficial = item.source_type === "official";

                return (
                  <div
                    key={item.id}
                    className={cn(
                      "rounded-2xl border bg-white p-4 sm:p-5 transition-all shadow-sm hover:shadow-md flex flex-col sm:flex-row sm:items-center gap-4",
                      isPast && "opacity-75 bg-gray-50/50",
                      item.is_completed && "bg-emerald-50/30 border-emerald-100"
                    )}
                  >
                    {/* Left Icon or Checkbox */}
                    <div className="flex items-center gap-3">
                      {isOfficial ? (
                        <div
                          className={cn(
                            "w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 text-xs font-bold",
                            isPast ? "bg-gray-100 text-gray-500" : "bg-blue-100 text-blue-700"
                          )}
                          title="Official Counselling Milestone"
                        >
                          🏛️
                        </div>
                      ) : (
                        <button
                          onClick={() => toggleTaskMutation.mutate(item.id)}
                          className={cn(
                            "w-7 h-7 rounded-lg border-2 flex items-center justify-center transition-colors cursor-pointer flex-shrink-0",
                            item.is_completed
                              ? "bg-emerald-500 border-emerald-500 text-white"
                              : "border-gray-300 hover:border-brand-500 bg-white"
                          )}
                          title={item.is_completed ? "Mark incomplete" : "Mark completed"}
                        >
                          {item.is_completed && (
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </button>
                      )}

                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3
                            className={cn(
                              "font-semibold text-base text-gray-900",
                              item.is_completed && "line-through text-gray-500"
                            )}
                          >
                            {item.event_name}
                          </h3>
                          {/* Badges */}
                          {isOfficial ? (
                            <span className="text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full">
                              Official Authority
                            </span>
                          ) : (
                            <span className="text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full">
                              Family Task
                            </span>
                          )}

                          {item.exam_type && (
                            <span className="text-[11px] font-medium bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                              {item.exam_type}
                              {item.round_number ? ` · Round ${item.round_number}` : ""}
                            </span>
                          )}
                        </div>

                        {item.notes && (
                          <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                            {item.notes}
                          </p>
                        )}

                        <div className="flex items-center gap-2 mt-1.5 text-xs text-gray-400">
                          <span className="font-medium text-gray-500">Source:</span>
                          <span className="italic">{item.source_citation}</span>
                        </div>
                      </div>
                    </div>

                    {/* Right Date and Actions */}
                    <div className="flex items-center justify-between sm:justify-end gap-3 sm:ml-auto pt-2 sm:pt-0 border-t sm:border-t-0 border-gray-100">
                      <div className="text-right">
                        <p className="text-sm font-semibold text-gray-900">
                          {item.event_date
                            ? new Date(item.event_date).toLocaleDateString("en-IN", {
                                day: "numeric",
                                month: "short",
                                year: "numeric",
                              })
                            : "Date TBD"}
                        </p>
                        <span
                          className={cn(
                            "inline-block text-[11px] font-semibold rounded-md px-2 py-0.5 mt-0.5",
                            isPast
                              ? "bg-gray-100 text-gray-500"
                              : isToday
                              ? "bg-red-100 text-red-700 font-bold"
                              : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          )}
                        >
                          {isToday ? "Due Today" : isPast ? t("overdue") || "Past" : daysLeft}
                        </span>
                      </div>

                      {item.can_delete && (
                        <button
                          onClick={() => deleteTaskMutation.mutate(item.id)}
                          className="p-1.5 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors cursor-pointer"
                          title="Delete task"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab: Document Checklist */}
      {(activeTab === "documents" || activeTab === "all") && (
        <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h2 className="text-xl font-bold text-gray-900">{t("checklistTitle") || "Mandatory Verification Documents"}</h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Keep these original documents and photocopies ready for certificate verification rounds.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-gray-700">
                {completedDocs} of {totalDocs} completed
              </span>
              <span className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full font-bold">
                {docPct}%
              </span>
            </div>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
            <div
              className="bg-emerald-500 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${docPct}%` }}
            />
          </div>

          {isLoadingChecklist ? (
            <div className="py-6 text-center text-gray-400">Loading checklist items...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
              {checklist.map((item) => (
                <div
                  key={item.id}
                  className={cn(
                    "rounded-xl border p-3.5 flex items-center gap-3 transition-colors",
                    item.is_completed
                      ? "bg-emerald-50/20 border-emerald-200"
                      : "bg-gray-50/50 border-gray-200"
                  )}
                >
                  <button
                    onClick={() => toggleChecklistMutation.mutate(item.id)}
                    className={cn(
                      "w-5 h-5 rounded border-2 flex-shrink-0 flex items-center justify-center transition-colors cursor-pointer",
                      item.is_completed
                        ? "bg-emerald-500 border-emerald-500 text-white"
                        : "border-gray-300 hover:border-emerald-500 bg-white"
                    )}
                    aria-label={item.is_completed ? "Mark incomplete" : "Mark done"}
                  >
                    {item.is_completed && (
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 12 12">
                        <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
                      </svg>
                    )}
                  </button>

                  <span
                    className={cn(
                      "text-sm font-medium flex-1",
                      item.is_completed ? "line-through text-gray-400" : "text-gray-800"
                    )}
                  >
                    {item.document_name}
                  </span>

                  <span
                    className={cn(
                      "text-[10px] font-semibold rounded-full px-2 py-0.5 border flex-shrink-0",
                      item.is_mandatory
                        ? "bg-rose-50 text-rose-700 border-rose-200"
                        : "bg-gray-100 text-gray-600 border-gray-200"
                    )}
                  >
                    {item.is_mandatory ? t("mandatory") || "Mandatory" : t("optional") || "Optional"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Add Custom Reminder Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-gray-100 pb-4">
              <div>
                <h3 className="text-xl font-bold text-gray-900">Add Admission Reminder</h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Set personal milestones or key counselling dates for your family.
                </p>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-gray-400 hover:text-gray-600 p-1.5 rounded-lg hover:bg-gray-100 cursor-pointer"
              >
                ✕
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl">
                {formError}
              </div>
            )}

            {/* Quick Presets */}
            <div className="space-y-1.5">
              <p className="text-xs font-semibold text-gray-500">Quick Templates:</p>
              <div className="flex flex-wrap gap-1.5">
                <button
                  type="button"
                  onClick={() => applyPreset("Pay Seat Acceptance Fee", "College Allotment Order")}
                  className="text-[11px] bg-brand-50 hover:bg-brand-100 text-brand-700 px-2.5 py-1 rounded-lg font-medium transition-colors cursor-pointer"
                >
                  💳 Seat Acceptance Fee
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset("Collect Transfer & Conduct Certificate", "Junior College Principal")}
                  className="text-[11px] bg-brand-50 hover:bg-brand-100 text-brand-700 px-2.5 py-1 rounded-lg font-medium transition-colors cursor-pointer"
                >
                  📜 Collect TC & Study Certs
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset("Report in-person to Allotted College", "Allotment Letter clause 3")}
                  className="text-[11px] bg-brand-50 hover:bg-brand-100 text-brand-700 px-2.5 py-1 rounded-lg font-medium transition-colors cursor-pointer"
                >
                  🏫 Physical Reporting
                </button>
              </div>
            </div>

            <form onSubmit={handleCreateTask} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Task Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Verify Income Certificate at MeeSeva / Tahsildar"
                  value={taskForm.title}
                  onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })}
                  className="w-full px-3.5 py-2 text-sm border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Due Date
                </label>
                <input
                  type="date"
                  value={taskForm.due_date}
                  onChange={(e) => setTaskForm({ ...taskForm, due_date: e.target.value })}
                  className="w-full px-3.5 py-2 text-sm border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Source / Citation
                </label>
                <input
                  type="text"
                  placeholder="e.g. APSCHE Official Notification / College Brochure"
                  value={taskForm.source_citation}
                  onChange={(e) => setTaskForm({ ...taskForm, source_citation: e.target.value })}
                  className="w-full px-3.5 py-2 text-sm border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Notes / Description (Optional)
                </label>
                <textarea
                  rows={2}
                  placeholder="e.g. Need 3 sets of attested Xerox copies and 4 passport photos."
                  value={taskForm.description}
                  onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })}
                  className="w-full px-3.5 py-2 text-sm border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-sm font-semibold text-gray-600 hover:text-gray-800 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createTaskMutation.isPending}
                  className="px-5 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-sm font-semibold transition-all shadow-sm cursor-pointer disabled:opacity-50"
                >
                  {createTaskMutation.isPending ? "Adding..." : "Add Reminder"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
