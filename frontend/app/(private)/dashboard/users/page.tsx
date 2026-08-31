"use client";

import { useEffect, useState } from "react";
import { Check, ChevronDown, Plus, Shield, Trash2, UserRound, X } from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { Avatar } from "@/app/_components/ui/avatar";
import { authService, type AccountRecord, type PermissionRecord, type RoleRecord } from "@/app/services/auth.service";
import type { SellerProfile } from "@/app/services/seller.service";
import { adminService } from "@/app/services/admin.service";

// The backend has no generic "list all accounts" endpoint yet.
// We derive users from the sellers list (which has account_id) plus
// the roles/permissions catalog which is admin-accessible.

const roleChipClasses: Record<string, string> = {
  admin: "bg-[#fbe6e0] text-[#b74d3b]",
  seller: "bg-[#e8f4ed] text-[#2d7a5e]",
  buyer: "bg-[#e4edfa] text-[#577ebd]",
};

export default function UsersPage() {
  const [accounts, setAccounts] = useState<AccountRecord[]>([]);
  const [sellers, setSellers] = useState<SellerProfile[]>([]);
  const [allRoles, setAllRoles] = useState<RoleRecord[]>([]);
  const [allPermissions, setAllPermissions] = useState<PermissionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Expanded account panel
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [accountRoles, setAccountRoles] = useState<Record<string, RoleRecord[]>>({});
  const [accountPerms, setAccountPerms] = useState<Record<string, string[]>>({});
  const [loadingAccount, setLoadingAccount] = useState(false);

  // Role management
  const [assignRoleTarget, setAssignRoleTarget] = useState<string | null>(null);
  const [selectedRole, setSelectedRole] = useState("");

  // Permission management
  const [assignPermTarget, setAssignPermTarget] = useState<string | null>(null);
  const [selectedPerm, setSelectedPerm] = useState("");

  // Roles/permissions admin tab
  const [adminTab, setAdminTab] = useState<"accounts" | "roles" | "permissions">("accounts");
  const [rolePerms, setRolePerms] = useState<Record<string, PermissionRecord[]>>({});
  const [expandedRole, setExpandedRole] = useState<string | null>(null);
  const [newRoleName, setNewRoleName] = useState("");
  const [newRoleDesc, setNewRoleDesc] = useState("");
  const [editingRole, setEditingRole] = useState<RoleRecord | null>(null);
  const [roleEditForm, setRoleEditForm] = useState({ name: "", description: "" });
  const [newPerm, setNewPerm] = useState({ code: "", name: "", resource: "", action: "", description: "" });
  const [editingPerm, setEditingPerm] = useState<PermissionRecord | null>(null);
  const [permEditForm, setPermEditForm] = useState({ name: "", resource: "", action: "", description: "" });
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState("");

  function flash(msg: string) { setSuccess(msg); setTimeout(() => setSuccess(""), 3000); }

  async function loadAll() {
    setLoading(true);
    try {
      const [accountsList, sellerList, roles, perms] = await Promise.all([
        authService.listAccounts(),
        adminService.listSellers(),
        authService.listRoles(),
        authService.listPermissions(),
      ]);
      setAccounts(accountsList);
      setSellers(sellerList);
      setAllRoles(roles);
      setAllPermissions(perms);
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      authService.listAccounts(),
      adminService.listSellers(),
      authService.listRoles(),
      authService.listPermissions(),
    ])
      .then(([accountsList, sellerList, roles, perms]) => {
        if (!cancelled) {
          setAccounts(accountsList);
          setSellers(sellerList);
          setAllRoles(roles);
          setAllPermissions(perms);
          setError("");
        }
      })
      .catch((caught) => { if (!cancelled) setError(caught instanceof Error ? caught.message : "Data could not be loaded."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  async function toggleAccount(accountId: string) {
    if (expandedId === accountId) { setExpandedId(null); return; }
    setExpandedId(accountId);
    if (!accountRoles[accountId]) {
      setLoadingAccount(true);
      try {
        const [roles, perms] = await Promise.all([
          authService.listAccountRoles(accountId),
          authService.listDirectPermissions(accountId),
        ]);
        setAccountRoles((p) => ({ ...p, [accountId]: roles }));
        setAccountPerms((p) => ({ ...p, [accountId]: perms }));
      } catch { /* ignore */ } finally { setLoadingAccount(false); }
    }
  }

  async function assignRole(accountId: string) {
    if (!selectedRole) return;
    setSaving(true);
    try {
      await authService.assignRoleToAccount(accountId, selectedRole);
      const roles = await authService.listAccountRoles(accountId);
      setAccountRoles((p) => ({ ...p, [accountId]: roles }));
      setAssignRoleTarget(null); setSelectedRole("");
      flash("Role assigned.");
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Role assignment failed."); } finally { setSaving(false); }
  }

  async function revokeRole(accountId: string, roleName: string) {
    try {
      await authService.revokeRoleFromAccount(accountId, roleName);
      const roles = await authService.listAccountRoles(accountId);
      setAccountRoles((p) => ({ ...p, [accountId]: roles }));
      flash("Role revoked.");
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Role revocation failed."); }
  }

  async function grantPerm(accountId: string) {
    if (!selectedPerm) return;
    setSaving(true);
    try {
      await authService.grantDirectPermission(accountId, selectedPerm);
      const perms = await authService.listDirectPermissions(accountId);
      setAccountPerms((p) => ({ ...p, [accountId]: perms }));
      setAssignPermTarget(null); setSelectedPerm("");
      flash("Permission granted.");
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Permission grant failed."); } finally { setSaving(false); }
  }

  async function revokePerm(accountId: string, code: string) {
    try {
      await authService.revokeDirectPermission(accountId, code);
      const perms = await authService.listDirectPermissions(accountId);
      setAccountPerms((p) => ({ ...p, [accountId]: perms }));
      flash("Permission revoked.");
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Permission revocation failed."); }
  }

  async function toggleRolePerms(roleName: string) {
    if (expandedRole === roleName) { setExpandedRole(null); return; }
    setExpandedRole(roleName);
    if (!rolePerms[roleName]) {
      try {
        const perms = await authService.listRolePermissions(roleName);
        setRolePerms((p) => ({ ...p, [roleName]: perms }));
      } catch { setRolePerms((p) => ({ ...p, [roleName]: [] })); }
    }
  }

  async function createRole(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await authService.createRole(newRoleName, newRoleDesc || undefined);
      setNewRoleName(""); setNewRoleDesc("");
      flash("Role created.");
      await loadAll();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Role could not be created."); } finally { setSaving(false); }
  }

  async function deleteRole(name: string) {
    try { await authService.deleteRole(name); flash("Role deleted."); await loadAll(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Role could not be deleted."); }
  }

  async function createPermission(e: React.FormEvent) {
    e.preventDefault();
    if (!newPerm.code || !newPerm.name || !newPerm.resource || !newPerm.action) { setError("Code, name, resource and action are required."); return; }
    setSaving(true);
    try {
      await authService.createPermission({
        code: newPerm.code,
        name: newPerm.name,
        resource: newPerm.resource,
        action: newPerm.action,
        description: newPerm.description || undefined,
      });
      setNewPerm({ code: "", name: "", resource: "", action: "", description: "" });
      flash("Permission created.");
      await loadAll();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Permission could not be created."); } finally { setSaving(false); }
  }

  async function deletePermission(code: string) {
    try { await authService.deletePermission(code); flash("Permission deleted."); await loadAll(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Permission could not be deleted."); }
  }

  async function startEditRole(role: RoleRecord) {
    setEditingRole(role);
    setRoleEditForm({ name: role.name, description: role.description ?? "" });
  }

  async function saveRole(e: React.FormEvent) {
    e.preventDefault();
    if (!editingRole) return;
    setSaving(true);
    try {
      await authService.updateRole(editingRole.name, { name: roleEditForm.name, description: roleEditForm.description || null });
      setEditingRole(null);
      flash("Role updated.");
      await loadAll();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Role could not be updated."); } finally { setSaving(false); }
  }

  async function startEditPerm(perm: PermissionRecord) {
    setEditingPerm(perm);
    setPermEditForm({ name: perm.name, resource: perm.resource, action: perm.action, description: perm.description ?? "" });
  }

  async function savePermission(e: React.FormEvent) {
    e.preventDefault();
    if (!editingPerm) return;
    setSaving(true);
    try {
      await authService.updatePermission(editingPerm.code, {
        name: permEditForm.name,
        resource: permEditForm.resource,
        action: permEditForm.action,
        description: permEditForm.description || null,
      });
      setEditingPerm(null);
      flash("Permission updated.");
      await loadAll();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Permission could not be updated."); } finally { setSaving(false); }
  }

  async function assignPermToRole(roleName: string, permCode: string) {
    try {
      await authService.assignPermissionToRole(roleName, permCode);
      const perms = await authService.listRolePermissions(roleName);
      setRolePerms((p) => ({ ...p, [roleName]: perms }));
      flash("Permission assigned to role.");
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Assignment failed."); }
  }

  async function revokePermFromRole(roleName: string, permCode: string) {
    try {
      await authService.revokePermissionFromRole(roleName, permCode);
      const perms = await authService.listRolePermissions(roleName);
      setRolePerms((p) => ({ ...p, [roleName]: perms }));
      flash("Permission revoked from role.");
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Revocation failed."); }
  }

  const tabs = [
    { key: "accounts" as const, label: "Accounts", count: accounts.length },
    { key: "roles" as const, label: "Roles", count: allRoles.length },
    { key: "permissions" as const, label: "Permissions", count: allPermissions.length },
  ];

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div>
        <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Admin workspace</p>
        <h1 className="mt-1 text-3xl font-black tracking-[-.04em]">Users & access</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">Manage accounts, roles, and permissions across the platform.</p>
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}
      {success && <p className="rounded-lg bg-[#e8f4ed] px-4 py-3 text-sm text-[#2d7a5e] flex items-center gap-2"><Check size={14} /> {success}</p>}

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl border border-[var(--line)] bg-[#f9fbf9] p-1 w-fit">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setAdminTab(t.key)}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-bold transition-colors ${adminTab === t.key ? "bg-white shadow-sm text-[var(--ink)]" : "text-[var(--muted)] hover:text-[var(--ink)]"}`}
          >
            {t.label}
            <span className={`rounded-full px-1.5 py-0.5 text-[10px] ${adminTab === t.key ? "bg-[#e8f4ed] text-[#2d7a5e]" : "bg-[var(--line)] text-[var(--muted)]"}`}>{t.count}</span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="rounded-xl border border-[var(--line)] bg-white p-10 text-center text-sm text-[var(--muted)]">Loading...</div>
      ) : (
        <>
          {/* ── ACCOUNTS TAB ── */}
          {adminTab === "accounts" && (
            <div className="space-y-3">
              {accounts.length === 0 ? (
                <div className="rounded-xl border border-dashed border-[var(--line)] bg-white p-12 text-center">
                  <UserRound className="mx-auto text-[#9aa9a1]" size={28} />
                  <p className="mt-3 text-sm text-[var(--muted)]">No accounts registered yet.</p>
                </div>
              ) : accounts.map((account) => {
                const accountId = account.id;
                const seller = sellers.find((s) => s.account_id === accountId);
                const isExpanded = expandedId === accountId;
                const roles = accountRoles[accountId];
                const perms = accountPerms[accountId];
                const initials = seller ? seller.business_name.slice(0, 2).toUpperCase() : account.email.slice(0, 2).toUpperCase();

                return (
                  <article key={accountId} className="rounded-xl border border-[var(--line)] bg-white overflow-hidden">
                    <div className="flex items-center gap-4 p-5">
                      <Avatar initials={initials} size="md" color={seller ? "#39836e" : "#829eb8"} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-bold text-[var(--ink)]">{seller?.business_name ?? account.email}</p>
                          {seller && <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold capitalize ${seller.status === "active" ? "bg-[#e8f4ed] text-[#2d7a5e]" : "bg-[#f2f5f2] text-[#7e8b84]"}`}>seller · {seller.status}</span>}
                        </div>
                        <p className="mt-0.5 text-xs text-[var(--muted)] truncate">{account.email}{account.phone ? ` · ${account.phone}` : ""}</p>
                        <div className="mt-2 flex flex-wrap items-center gap-1">
                          {account.roles.map((role) => (
                            <span key={role} className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${roleChipClasses[role] ?? "bg-[#f2f5f2] text-[#7e8b84]"}`}>{role}</span>
                          ))}
                          {account.is_verified ? (
                            <span className="rounded-full bg-[#e4edfa] px-2 py-0.5 text-[10px] font-bold text-[#577ebd]">verified</span>
                          ) : (
                            <span className="rounded-full bg-[#f8e8dc] px-2 py-0.5 text-[10px] font-bold text-[#b0783d]">unverified</span>
                          )}
                          {!account.is_active && <span className="rounded-full bg-[#fbe6e0] px-2 py-0.5 text-[10px] font-bold text-[#b74d3b]">disabled</span>}
                        </div>
                      </div>
                      <button
                        onClick={() => toggleAccount(accountId)}
                        className="shrink-0 rounded-lg border border-[var(--line)] p-2 text-[var(--muted)] hover:bg-[#f9fbf9] transition-colors"
                      >
                        <ChevronDown size={15} className={`transition-transform ${isExpanded ? "rotate-180" : ""}`} />
                      </button>
                    </div>

                    {isExpanded && (
                      <div className="border-t border-[var(--line)] p-5 space-y-5">
                        {loadingAccount && !roles ? (
                          <p className="text-xs text-[var(--muted)]">Loading account details...</p>
                        ) : (
                          <>
                            {/* Roles */}
                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <p className="text-xs font-bold text-[var(--ink)]">Roles</p>
                                <button
                                  onClick={() => setAssignRoleTarget(assignRoleTarget === accountId ? null : accountId)}
                                  className="flex items-center gap-1 text-[11px] font-bold text-[var(--teal)] hover:underline"
                                >
                                  <Plus size={12} /> Assign role
                                </button>
                              </div>
                              <div className="flex flex-wrap gap-2">
                                {(roles ?? []).map((r) => (
                                  <span key={r.name} className="flex items-center gap-1.5 rounded-full border border-[var(--line)] bg-[#f9fbf9] px-3 py-1 text-[11px] font-bold">
                                    {r.name}
                                    <button onClick={() => revokeRole(accountId, r.name)} className="text-[var(--muted)] hover:text-[#b74d3b]"><X size={11} /></button>
                                  </span>
                                ))}
                                {(roles ?? []).length === 0 && <p className="text-xs text-[var(--muted)]">No roles assigned.</p>}
                              </div>
                              {assignRoleTarget === accountId && (
                                <div className="mt-3 flex gap-2">
                                  <select
                                    value={selectedRole}
                                    onChange={(e) => setSelectedRole(e.target.value)}
                                    className="flex-1 h-9 rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]"
                                  >
                                    <option value="">Select role...</option>
                                    {allRoles.map((r) => <option key={r.name} value={r.name}>{r.name}</option>)}
                                  </select>
                                  <Button size="sm" disabled={!selectedRole || saving} onClick={() => assignRole(accountId)}>
                                    <Check size={13} /> Assign
                                  </Button>
                                  <Button size="sm" variant="outline" onClick={() => setAssignRoleTarget(null)}><X size={13} /></Button>
                                </div>
                              )}
                            </div>

                            {/* Direct permissions */}
                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <p className="text-xs font-bold text-[var(--ink)]">Direct permissions</p>
                                <button
                                  onClick={() => setAssignPermTarget(assignPermTarget === accountId ? null : accountId)}
                                  className="flex items-center gap-1 text-[11px] font-bold text-[var(--teal)] hover:underline"
                                >
                                  <Plus size={12} /> Grant permission
                                </button>
                              </div>
                              <div className="flex flex-wrap gap-2">
                                {(perms ?? []).map((code) => (
                                  <span key={code} className="flex items-center gap-1.5 rounded-full border border-[var(--line)] bg-[#f9fbf9] px-3 py-1 text-[11px] font-mono">
                                    {code}
                                    <button onClick={() => revokePerm(accountId, code)} className="text-[var(--muted)] hover:text-[#b74d3b]"><X size={11} /></button>
                                  </span>
                                ))}
                                {(perms ?? []).length === 0 && <p className="text-xs text-[var(--muted)]">No direct permissions.</p>}
                              </div>
                              {assignPermTarget === accountId && (
                                <div className="mt-3 flex gap-2">
                                  <select
                                    value={selectedPerm}
                                    onChange={(e) => setSelectedPerm(e.target.value)}
                                    className="flex-1 h-9 rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]"
                                  >
                                    <option value="">Select permission...</option>
                                    {allPermissions.map((p) => <option key={p.code} value={p.code}>{p.code}</option>)}
                                  </select>
                                  <Button size="sm" disabled={!selectedPerm || saving} onClick={() => grantPerm(accountId)}>
                                    <Check size={13} /> Grant
                                  </Button>
                                  <Button size="sm" variant="outline" onClick={() => setAssignPermTarget(null)}><X size={13} /></Button>
                                </div>
                              )}
                            </div>
                          </>
                        )}
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          )}

          {/* ── ROLES TAB ── */}
          {adminTab === "roles" && (
            <div className="grid gap-6 lg:grid-cols-[1fr_1.6fr]">
              <div className="rounded-xl border border-[var(--line)] bg-white p-6">
                <h2 className="font-bold">Create role</h2>
                <form onSubmit={createRole} className="mt-4 space-y-3">
                  <input required value={newRoleName} onChange={(e) => setNewRoleName(e.target.value)} placeholder="Role name (e.g. moderator)" className="flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]" />
                  <input value={newRoleDesc} onChange={(e) => setNewRoleDesc(e.target.value)} placeholder="Description (optional)" className="flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]" />
                  <Button type="submit" disabled={saving}><Plus size={14} /> Create role</Button>
                </form>
              </div>
              <div className="rounded-xl border border-[var(--line)] bg-white overflow-hidden">
                <div className="border-b border-[var(--line)] bg-[#f9fbf9] px-5 py-3">
                  <p className="text-xs font-bold">All roles ({allRoles.length})</p>
                </div>
                <div className="divide-y divide-[#eff1ef]">
                  {allRoles.map((role) => (
                    <div key={role.name} className="overflow-hidden">
                      <div className="flex items-center gap-3 px-5 py-4">
                        <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#e8f4ed] text-[var(--teal)]"><Shield size={14} /></div>
                        <div className="flex-1 min-w-0">
                          <p className="font-bold text-sm">{role.name}</p>
                          {role.description && <p className="text-xs text-[var(--muted)]">{role.description}</p>}
                        </div>
                        <div className="flex gap-2 shrink-0">
                          <button onClick={() => toggleRolePerms(role.name)} className="text-[11px] font-bold text-[var(--teal)] hover:underline">
                            {expandedRole === role.name ? "Hide" : "Permissions"}
                          </button>
                          <button onClick={() => startEditRole(role)} className="text-[11px] font-bold text-[var(--ink)] hover:underline">Edit</button>
                          <button onClick={() => deleteRole(role.name)} className="text-[var(--muted)] hover:text-[#b74d3b]"><Trash2 size={13} /></button>
                        </div>
                      </div>
                      {editingRole?.name === role.name && (
                        <form onSubmit={saveRole} className="border-t border-[var(--line)] bg-[#f9fbf9] px-5 py-4 space-y-3">
                          <div className="grid gap-3 sm:grid-cols-2">
                            <input
                              required
                              value={roleEditForm.name}
                              onChange={(e) => setRoleEditForm((f) => ({ ...f, name: e.target.value }))}
                              placeholder="Role name"
                              className="flex h-9 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]"
                            />
                            <input
                              value={roleEditForm.description}
                              onChange={(e) => setRoleEditForm((f) => ({ ...f, description: e.target.value }))}
                              placeholder="Description (optional)"
                              className="flex h-9 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]"
                            />
                          </div>
                          <div className="flex gap-2">
                            <Button type="submit" size="sm" disabled={saving}><Check size={13} /> Save</Button>
                            <Button type="button" size="sm" variant="outline" onClick={() => setEditingRole(null)}><X size={13} /> Cancel</Button>
                          </div>
                        </form>
                      )}
                      {expandedRole === role.name && (
                        <div className="border-t border-[var(--line)] bg-[#f9fbf9] px-5 py-4 space-y-3">
                          <div className="flex flex-wrap gap-2">
                            {(rolePerms[role.name] ?? []).map((p) => (
                              <span key={p.code} className="flex items-center gap-1.5 rounded-full border border-[var(--line)] bg-white px-3 py-1 text-[11px] font-mono">
                                {p.code}
                                <button onClick={() => revokePermFromRole(role.name, p.code)} className="text-[var(--muted)] hover:text-[#b74d3b]"><X size={11} /></button>
                              </span>
                            ))}
                            {(rolePerms[role.name] ?? []).length === 0 && <p className="text-xs text-[var(--muted)]">No permissions assigned.</p>}
                          </div>
                          <div className="flex gap-2">
                            <select
                              onChange={(e) => { if (e.target.value) assignPermToRole(role.name, e.target.value); e.target.value = ""; }}
                              className="flex-1 h-9 rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]"
                              defaultValue=""
                            >
                              <option value="">Add permission to role...</option>
                              {allPermissions.map((p) => <option key={p.code} value={p.code}>{p.code}</option>)}
                            </select>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ── PERMISSIONS TAB ── */}
          {adminTab === "permissions" && (
            <div className="grid gap-6 lg:grid-cols-[1fr_1.6fr]">
              <div className="rounded-xl border border-[var(--line)] bg-white p-6">
                <h2 className="font-bold">Create permission</h2>
                <p className="mt-1 text-xs text-[var(--muted)]">Permissions are code-defined and synced. Only create here if you need a custom one not in the codebase.</p>
                <form onSubmit={createPermission} className="mt-4 space-y-3">
                  <input required value={newPerm.code} onChange={(e) => setNewPerm((p) => ({ ...p, code: e.target.value }))} placeholder="Code (e.g. products.create)" className="flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]" />
                  <input required value={newPerm.name} onChange={(e) => setNewPerm((p) => ({ ...p, name: e.target.value }))} placeholder="Name (e.g. Create products)" className="flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]" />
                  <div className="grid grid-cols-2 gap-3">
                    <input required value={newPerm.resource} onChange={(e) => setNewPerm((p) => ({ ...p, resource: e.target.value }))} placeholder="Resource (e.g. products)" className="flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]" />
                    <input required value={newPerm.action} onChange={(e) => setNewPerm((p) => ({ ...p, action: e.target.value }))} placeholder="Action (e.g. create)" className="flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]" />
                  </div>
                  <input value={newPerm.description} onChange={(e) => setNewPerm((p) => ({ ...p, description: e.target.value }))} placeholder="Description (optional)" className="flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]" />
                  <Button type="submit" disabled={saving}><Plus size={14} /> Create permission</Button>
                </form>
              </div>
              <div className="rounded-xl border border-[var(--line)] bg-white overflow-hidden">
                <div className="border-b border-[var(--line)] bg-[#f9fbf9] px-5 py-3">
                  <p className="text-xs font-bold">All permissions ({allPermissions.length})</p>
                </div>
                <div className="divide-y divide-[#eff1ef] max-h-[500px] overflow-y-auto">
                  {allPermissions.map((perm) => (
                    <div key={perm.code} className="overflow-hidden">
                      <div className="flex items-center gap-3 px-5 py-3">
                        <div className="flex-1 min-w-0">
                          <p className="font-mono text-xs font-bold text-[var(--ink)]">{perm.code}</p>
                          <div className="mt-0.5 flex flex-wrap items-center gap-1.5">
                            <span className="text-xs text-[var(--muted)]">{perm.name}</span>
                            <span className="rounded-full bg-[#f2f5f2] px-1.5 py-0.5 text-[9px] font-bold text-[#7e8b84]">{perm.resource} · {perm.action}</span>
                            {perm.description && <span className="text-[11px] text-[var(--muted)]">{perm.description}</span>}
                          </div>
                        </div>
                        <div className="flex gap-2 shrink-0">
                          <button onClick={() => startEditPerm(perm)} className="text-[11px] font-bold text-[var(--ink)] hover:underline">Edit</button>
                          <button onClick={() => deletePermission(perm.code)} className="text-[var(--muted)] hover:text-[#b74d3b]"><Trash2 size={13} /></button>
                        </div>
                      </div>
                      {editingPerm?.code === perm.code && (
                        <form onSubmit={savePermission} className="border-t border-[var(--line)] bg-[#f9fbf9] px-5 py-4 space-y-3">
                          <input required value={permEditForm.name} onChange={(e) => setPermEditForm((f) => ({ ...f, name: e.target.value }))} placeholder="Name" className="flex h-9 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]" />
                          <div className="grid grid-cols-2 gap-3">
                            <input required value={permEditForm.resource} onChange={(e) => setPermEditForm((f) => ({ ...f, resource: e.target.value }))} placeholder="Resource" className="flex h-9 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]" />
                            <input required value={permEditForm.action} onChange={(e) => setPermEditForm((f) => ({ ...f, action: e.target.value }))} placeholder="Action" className="flex h-9 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]" />
                          </div>
                          <input value={permEditForm.description} onChange={(e) => setPermEditForm((f) => ({ ...f, description: e.target.value }))} placeholder="Description (optional)" className="flex h-9 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]" />
                          <div className="flex gap-2">
                            <Button type="submit" size="sm" disabled={saving}><Check size={13} /> Save</Button>
                            <Button type="button" size="sm" variant="outline" onClick={() => setEditingPerm(null)}><X size={13} /> Cancel</Button>
                          </div>
                        </form>
                      )}
                    </div>
                  ))}
                  {allPermissions.length === 0 && <p className="px-5 py-4 text-xs text-[var(--muted)]">No permissions yet. Run the sync script to populate from code.</p>}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
