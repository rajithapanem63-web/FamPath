"use client";

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/authStore";
import { useWorkspaceStore } from "@/stores/workspaceStore";
import { get, post, put } from "@/lib/api";
import { Link } from "@/i18n/routing";
import { getInitials, cn } from "@/lib/utils";
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, Cell
} from "recharts";

interface WorkspaceMember {
  user_id: string;
  full_name: string | null;
  email: string;
  role: string;
  consent_given: boolean;
  joined_at: string | null;
}

interface WorkspaceDetail {
  id: string;
  name: string;
  owner_id: string;
  status: string;
  members: WorkspaceMember[];
}

interface CareerSkill {
  name: string;
  category: string;
  level: string;
}

interface CareerMilestone {
  id: string;
  text: string;
}

interface CareerStage {
  stage: number;
  title: string;
  milestones: CareerMilestone[];
}

interface BeginnerProject {
  title: string;
  desc: string;
}

interface CareerRoadmapResponse {
  has_goal: boolean;
  branch_code?: string;
  career_role?: string;
  current_semester?: number;
  completed_milestones?: string[];
  progress_percent?: number;
  description?: string;
  skills?: CareerSkill[];
  roadmap?: CareerStage[];
  beginner_projects?: BeginnerProject[];
  available_options?: Record<string, string[]>;
}

export default function DashboardPage() {
  const t = useTranslations("workspace");
  const { user } = useAuthStore();
  const { workspace, setWorkspace } = useWorkspaceStore();
  const qc = useQueryClient();

  // Modal / Inline forms state
  const [newWsName, setNewWsName] = useState("");
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("parent");
  const [inviteFeedback, setInviteFeedback] = useState<string | null>(null);

  // Career Goal Editing
  const [isGoalEditing, setIsGoalEditing] = useState(false);
  const [selectedBranch, setSelectedBranch] = useState("CSE");
  const [selectedRole, setSelectedRole] = useState("Full-Stack Web Development");

  // Query workspaces if active workspace is missing
  const { data: userWorkspaces = [] } = useQuery({
    queryKey: ["user-workspaces"],
    queryFn: () => get<Array<{ id: string; name: string; owner_id: string; status: string }>>("/workspaces"),
    enabled: !!user,
  });

  useEffect(() => {
    if (!workspace && userWorkspaces.length > 0) {
      const first = userWorkspaces[0];
      if (first) {
        setWorkspace(first);
      }
    }
  }, [workspace, userWorkspaces, setWorkspace]);

  // Workspace Detail
  const { data: wsDetail, isLoading: isWsLoading } = useQuery({
    queryKey: ["workspace", workspace?.id],
    queryFn: () => get<WorkspaceDetail>(`/workspaces/${workspace?.id}`),
    enabled: !!workspace?.id,
  });

  // Career Roadmap Query
  const { data: roadmapData, isLoading: isRoadmapLoading } = useQuery({
    queryKey: ["career-roadmap", workspace?.id],
    queryFn: () => get<CareerRoadmapResponse>(`/career-roadmap/${workspace?.id}`),
    enabled: !!workspace?.id,
  });

  // Alignment Score Query
  const { data: alignmentData } = useQuery<{ alignment_score: number | null; dimension_scores: Record<string, number> | null }>({
    queryKey: ["alignment", workspace?.id],
    queryFn: () => get(`/alignment/${workspace?.id}`),
    enabled: !!workspace?.id,
    retry: false,
  });

  // Create Workspace Mutation
  const createWsMutation = useMutation({
    mutationFn: (name: string) =>
      post<{ id: string; name: string; owner_id: string; status: string }>("/workspaces", { name }),
    onSuccess: (data) => {
      setWorkspace(data);
      qc.invalidateQueries({ queryKey: ["user-workspaces"] });
      setNewWsName("");
    },
  });

  // Invite Member Mutation
  const inviteMutation = useMutation({
    mutationFn: () =>
      post(`/workspaces/${workspace?.id}/invitations`, {
        email: inviteEmail,
        role: inviteRole,
      }),
    onSuccess: () => {
      setInviteFeedback("✓ Invitation sent successfully!");
      setInviteEmail("");
      setTimeout(() => {
        setIsInviteOpen(false);
        setInviteFeedback(null);
      }, 2000);
    },
    onError: () => {
      setInviteFeedback("Failed to send invitation. Please verify the email.");
    },
  });

  // Set Career Goal Mutation
  const setGoalMutation = useMutation({
    mutationFn: () =>
      post(`/career-roadmap/${workspace?.id}`, {
        branch_code: selectedBranch,
        career_role: selectedRole,
        current_semester: 1,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["career-roadmap", workspace?.id] });
      setIsGoalEditing(false);
    },
  });

  // Toggle Milestone Mutation
  const toggleMilestoneMutation = useMutation({
    mutationFn: (mId: string) =>
      put(`/career-roadmap/${workspace?.id}/milestones/${mId}`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["career-roadmap", workspace?.id] });
    },
  });

  // If no workspace active and none returned, show inline creator
  if (!workspace) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center max-w-lg mx-auto space-y-6 animate-in fade-in">
        <div className="text-6xl">🏠</div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome to FamPath</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Create your shared family workspace to collaborate on engineering college predictions, costs, and career roadmaps.
          </p>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (newWsName.trim()) createWsMutation.mutate(newWsName.trim());
          }}
          className="w-full bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-4"
        >
          <div className="text-left">
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              {t("create.nameLabel")}
            </label>
            <input
              type="text"
              required
              value={newWsName}
              onChange={(e) => setNewWsName(e.target.value)}
              placeholder={t("create.namePlaceholder")}
              className="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <button
            type="submit"
            disabled={createWsMutation.isPending || !newWsName.trim()}
            className="w-full rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold py-2.5 text-sm transition shadow-sm disabled:opacity-60"
          >
            {createWsMutation.isPending ? "Creating Workspace…" : t("create.submitButton")}
          </button>
        </form>
      </div>
    );
  }

  const completedSet = new Set(roadmapData?.completed_milestones || []);

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{wsDetail?.name ?? workspace.name}</h1>
          <p className="text-muted-foreground text-sm mt-0.5">{t("dashboard.title")}</p>
        </div>
        <button
          onClick={() => setIsInviteOpen(true)}
          className="rounded-xl bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 text-sm font-semibold transition shadow-sm self-start sm:self-auto"
        >
          {t("dashboard.inviteButton")}
        </button>
      </div>

      {/* Invite Modal */}
      {isInviteOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md bg-white rounded-2xl shadow-xl border p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-gray-900">{t("invite.title")}</h3>
              <button onClick={() => setIsInviteOpen(false)} className="text-gray-400 hover:text-gray-700">✕</button>
            </div>
            {inviteFeedback ? (
              <p className={cn("text-sm p-3 rounded-lg font-medium", inviteFeedback.startsWith("✓") ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800")}>
                {inviteFeedback}
              </p>
            ) : (
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">{t("invite.emailLabel")}</label>
                  <input
                    type="email"
                    required
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="parent@example.com"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">{t("invite.roleLabel")}</label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm bg-white"
                  >
                    <option value="parent">{t("invite.roleParent")}</option>
                    <option value="counsellor">{t("invite.roleCounsellor")}</option>
                  </select>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button onClick={() => setIsInviteOpen(false)} className="px-4 py-2 text-xs font-medium text-gray-600">Cancel</button>
                  <button
                    onClick={() => inviteMutation.mutate()}
                    disabled={inviteMutation.isPending || !inviteEmail.trim()}
                    className="rounded-lg bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 text-xs font-semibold disabled:opacity-60"
                  >
                    {inviteMutation.isPending ? "Sending…" : t("invite.submitButton")}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Quick Action Navigation Grid (All 8 Platform Capabilities) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-8 gap-3">
        {[
          { href: "/preferences", icon: "⚙️", label: "Preferences" },
          { href: "/predict", icon: "🎯", label: "Predictor" },
          { href: "/aptitude", icon: "🧠", label: "Aptitude" },
          { href: "/alignment", icon: "🤝", label: "Alignment" },
          { href: "/shortlist", icon: "📋", label: "Shortlist" },
          { href: "/cost", icon: "💳", label: "Cost & Aid" },
          { href: "/chatbot", icon: "🤖", label: "FamPath AI" },
          { href: "/timeline", icon: "📅", label: "Timeline" },
        ].map(({ href, icon, label }) => (
          <Link
            key={href}
            href={href as "/"}
            className="flex flex-col items-center justify-center gap-1.5 rounded-xl border border-gray-200 bg-white p-3 hover:border-brand-300 hover:bg-brand-50/50 hover:shadow-sm transition text-center group"
          >
            <span className="text-2xl group-hover:scale-110 transition-transform">{icon}</span>
            <span className="text-xs font-semibold text-gray-800">{label}</span>
          </Link>
        ))}
      </div>

      {/* FAMILY ALIGNMENT CHART */}
      {alignmentData && (
        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b pb-4">
            <span className="text-2xl">🤝</span>
            <div>
              <h2 className="text-lg font-bold text-gray-900">Family Alignment</h2>
              <p className="text-xs text-muted-foreground">How well your family agrees on college priorities</p>
            </div>
            {alignmentData.alignment_score != null && (
              <div className="ml-auto text-right">
                <p className="text-2xl font-bold text-brand-600">{Math.round(alignmentData.alignment_score)}%</p>
                <p className="text-xs text-muted-foreground">Alignment Score</p>
              </div>
            )}
          </div>

          {alignmentData.dimension_scores && Object.keys(alignmentData.dimension_scores).length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Bar chart */}
              <div>
                <p className="text-xs font-semibold text-gray-600 mb-3">Dimension Scores</p>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={Object.entries(alignmentData.dimension_scores).map(([k, v]) => ({ name: k.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()).slice(0, 12), score: Math.round(v) }))}>
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                      {Object.entries(alignmentData.dimension_scores).map((_, i) => (
                        <Cell key={i} fill={i % 2 === 0 ? "#2563eb" : "#7c3aed"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              {/* Radar chart */}
              <div>
                <p className="text-xs font-semibold text-gray-600 mb-3">Alignment Radar</p>
                <ResponsiveContainer width="100%" height={200}>
                  <RadarChart data={Object.entries(alignmentData.dimension_scores).map(([k, v]) => ({ subject: k.replace(/_/g, " ").slice(0, 10), score: Math.round(v) }))}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="subject" tick={{ fontSize: 9 }} />
                    <Radar dataKey="score" stroke="#2563eb" fill="#2563eb" fillOpacity={0.3} />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          ) : (
            <div className="text-center py-6 text-muted-foreground text-sm">
              <p>Submit preferences to see family alignment charts.</p>
              <Link href="/preferences" className="text-brand-600 hover:underline text-xs mt-1 inline-block">Complete preferences →</Link>
            </div>
          )}
        </div>
      )}

      {/* FEATURE 4: CAREER ROADMAP (RULE-BASED LEARNING ENGINE) */}
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b pb-4 gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">🗺️</span>
              <h2 className="text-lg font-bold text-gray-900">Engineering Career Roadmap</h2>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Structured semester-by-semester skill acquisition, projects, and milestone tracking for your engineering target.
            </p>
          </div>

          <button
            onClick={() => setIsGoalEditing(!isGoalEditing)}
            className="rounded-lg border border-brand-200 bg-brand-50/60 text-brand-700 text-xs font-semibold px-3 py-1.5 hover:bg-brand-100 transition self-start sm:self-auto"
          >
            {isGoalEditing ? "Cancel" : "Change Career Goal"}
          </button>
        </div>

        {/* Goal Selector Form */}
        {isGoalEditing && (
          <div className="rounded-xl border border-brand-200 bg-brand-50/30 p-4 space-y-4 animate-in slide-in-from-top-2">
            <h3 className="text-xs font-bold text-brand-900 uppercase tracking-wider">
              Select Preferred Engineering Branch & Target Career Goal
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Engineering Branch</label>
                <select
                  value={selectedBranch}
                  onChange={(e) => {
                    const br = e.target.value;
                    setSelectedBranch(br);
                    if (br === "CSE") setSelectedRole("Full-Stack Web Development");
                    else if (br === "ECE") setSelectedRole("Embedded Systems & IoT");
                    else if (br === "MECH") setSelectedRole("CAD / CAM & Product Design");
                    else setSelectedRole("Core Engineering & Software Proficiency");
                  }}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-xs bg-white"
                >
                  <option value="CSE">Computer Science & Engineering (CSE)</option>
                  <option value="ECE">Electronics & Communication (ECE)</option>
                  <option value="MECH">Mechanical Engineering (MECH)</option>
                  <option value="EEE">Electrical & Electronics (EEE)</option>
                  <option value="CIVIL">Civil Engineering (CIVIL)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Target Career Role</label>
                <select
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-xs bg-white"
                >
                  {selectedBranch === "CSE" && (
                    <>
                      <option value="Full-Stack Web Development">Full-Stack Web Development</option>
                      <option value="Data Science & AI / ML">Data Science & AI / ML</option>
                    </>
                  )}
                  {selectedBranch === "ECE" && (
                    <option value="Embedded Systems & IoT">Embedded Systems & IoT</option>
                  )}
                  {selectedBranch === "MECH" && (
                    <option value="CAD / CAM & Product Design">CAD / CAM & Product Design</option>
                  )}
                  {(selectedBranch === "EEE" || selectedBranch === "CIVIL") && (
                    <option value="Core Engineering & Software Proficiency">Core Engineering & Software Proficiency</option>
                  )}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setGoalMutation.mutate()}
                disabled={setGoalMutation.isPending}
                className="rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs px-4 py-2 disabled:opacity-60"
              >
                {setGoalMutation.isPending ? "Saving…" : "Save Roadmap Target"}
              </button>
            </div>
          </div>
        )}

        {isRoadmapLoading ? (
          <div className="py-12 text-center text-xs text-muted-foreground">Loading career track…</div>
        ) : !roadmapData?.has_goal ? (
          <div className="text-center py-8 bg-gray-50 rounded-xl border border-dashed border-gray-300 space-y-3">
            <span className="text-4xl block">🎯</span>
            <p className="font-semibold text-sm text-gray-900">Define Your Engineering Career Vision</p>
            <p className="text-xs text-muted-foreground max-w-md mx-auto">
              Select your preferred branch and career track to generate ordered milestones and starter projects.
            </p>
            <button
              onClick={() => setIsGoalEditing(true)}
              className="rounded-lg bg-brand-600 text-white text-xs font-semibold px-4 py-2 hover:bg-brand-700 transition"
            >
              Choose My Career Track
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Active Track Banner & Progress */}
            <div className="bg-brand-50/50 border border-brand-200 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-brand-600 text-white text-[10px] font-bold px-2 py-0.5">
                    {roadmapData.branch_code}
                  </span>
                  <h3 className="font-bold text-gray-900 text-sm">{roadmapData.career_role}</h3>
                </div>
                <p className="text-xs text-gray-600 mt-1 max-w-xl">{roadmapData.description}</p>
              </div>

              {/* Progress Bar */}
              <div className="w-full md:w-56 space-y-1.5 flex-shrink-0">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-gray-700">Roadmap Progress</span>
                  <span className="text-brand-700">{roadmapData.progress_percent}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-brand-600 h-full rounded-full transition-all"
                    style={{ width: `${roadmapData.progress_percent}%` }}
                  />
                </div>
                <span className="text-[10px] text-muted-foreground">
                  {completedSet.size} steps completed
                </span>
              </div>
            </div>

            {/* Core Skills Chips */}
            {roadmapData.skills && (
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Target Technical Competencies
                </h4>
                <div className="flex flex-wrap gap-2">
                  {roadmapData.skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="rounded-lg bg-gray-100 border border-gray-200 px-2.5 py-1 text-xs text-gray-800 font-medium flex items-center gap-1.5"
                    >
                      <span className="text-brand-600 text-[10px] font-bold">●</span>
                      {skill.name}
                      <span className="text-[10px] text-gray-400">({skill.category})</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Ordered Stages & Milestones */}
            <div className="space-y-4">
              <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                Ordered Learning Roadmap
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {roadmapData.roadmap?.map((stage) => (
                  <div key={stage.stage} className="rounded-xl border border-gray-200 bg-gray-50/40 p-4 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-gray-900 text-white w-5 h-5 flex items-center justify-center text-[10px] font-bold">
                        {stage.stage}
                      </span>
                      <h5 className="font-bold text-xs text-gray-900">{stage.title}</h5>
                    </div>

                    <div className="space-y-2">
                      {stage.milestones.map((m) => {
                        const isDone = completedSet.has(m.id);
                        return (
                          <label
                            key={m.id}
                            className={cn(
                              "flex items-start gap-2.5 p-2 rounded-lg border text-xs cursor-pointer transition select-none",
                              isDone
                                ? "bg-green-50/70 border-green-200 text-green-950 font-medium"
                                : "bg-white border-gray-200 text-gray-700 hover:border-brand-300"
                            )}
                          >
                            <input
                              type="checkbox"
                              checked={isDone}
                              onChange={() => toggleMilestoneMutation.mutate(m.id)}
                              className="mt-0.5 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                            />
                            <span className={cn(isDone && "line-through opacity-80")}>{m.text}</span>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Beginner Projects Recommendations */}
            {roadmapData.beginner_projects && (
              <div className="space-y-3 pt-2">
                <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider flex items-center gap-1.5">
                  <span>🚀</span> Recommended Beginner Projects
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {roadmapData.beginner_projects.map((proj, idx) => (
                    <div key={idx} className="rounded-xl border border-gray-200 p-3.5 bg-white space-y-1 hover:border-brand-300 transition">
                      <p className="font-bold text-xs text-gray-900">{proj.title}</p>
                      <p className="text-[11px] text-gray-600 leading-relaxed">{proj.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Workspace Members Section */}
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
        <h2 className="text-base font-bold text-gray-900">
          {t("dashboard.members")} ({wsDetail?.members?.length ?? 0})
        </h2>

        {isWsLoading ? (
          <p className="text-muted-foreground text-xs">Loading members…</p>
        ) : wsDetail?.members?.length === 0 ? (
          <p className="text-muted-foreground text-xs">{t("dashboard.noMembers")}</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {wsDetail?.members?.map((member) => (
              <div
                key={member.user_id}
                className="flex items-center gap-3 rounded-xl border border-gray-200 p-3.5 bg-gray-50/50"
              >
                <div className="h-9 w-9 rounded-full bg-brand-100 flex items-center justify-center text-brand-700 font-semibold text-xs flex-shrink-0">
                  {getInitials(member.full_name ?? member.email)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-xs text-gray-900 truncate">
                    {member.full_name ?? member.email}
                  </p>
                  <p className="text-[10px] text-muted-foreground capitalize">{member.role}</p>
                </div>
                <span className={cn(
                  "text-[10px] px-2 py-0.5 rounded-full border font-medium flex-shrink-0",
                  member.consent_given
                    ? "bg-green-50 text-green-700 border-green-200"
                    : "bg-amber-50 text-amber-700 border-amber-200"
                )}>
                  {member.consent_given ? "Active" : "Pending"}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Development Seed Data Badge */}
      <div className="rounded-xl bg-amber-50 border border-amber-200 p-3.5 text-xs text-amber-800">
        <strong>FamPath Notice:</strong> College predictions, cutoff bands, and career roadmaps are decision-support aids based on official state syllabus benchmarks and verified gazettes.
      </div>
    </div>
  );
}
