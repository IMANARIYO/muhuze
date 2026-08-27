import { Card, CardContent } from "@/app/_components/ui/card";
import { Avatar } from "@/app/_components/ui/avatar";
import { users } from "@/app/lib/data";

const roleColors: Record<string, { bg: string; text: string; avatarColor: string }> = {
  client: { bg: "#e4edfa", text: "#577ebd", avatarColor: "#829eb8" },
  seller: { bg: "#e8f4ed", text: "#2d7a5e", avatarColor: "#39836e" },
  admin:  { bg: "#fbe6e0", text: "#d75e4a", avatarColor: "#d7896d" },
};

export default function UsersPage() {
  const sellers = users.filter((u) => u.role === "seller");
  const clients = users.filter((u) => u.role === "client");
  const admins  = users.filter((u) => u.role === "admin");

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-[var(--ink)]">Users</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Manage all platform users — clients, sellers, and admins.
        </p>
      </div>

      {/* Summary pills */}
      <div className="flex flex-wrap gap-3">
        <div className="rounded-full bg-[#e8f4ed] px-4 py-1.5 text-[11px] font-bold text-[#2d7a5e]">
          {sellers.length} Sellers
        </div>
        <div className="rounded-full bg-[#e4edfa] px-4 py-1.5 text-[11px] font-bold text-[#577ebd]">
          {clients.length} Clients
        </div>
        <div className="rounded-full bg-[#fbe6e0] px-4 py-1.5 text-[11px] font-bold text-[#d75e4a]">
          {admins.length} Admins
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[var(--line)] bg-[#f9fbf9]">
                  <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">User</th>
                  <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Email</th>
                  <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Role</th>
                  <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Joined</th>
                  <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#eff1ef]">
                {users.map((user) => {
                  const rc = roleColors[user.role];
                  return (
                    <tr key={user.id} className="hover:bg-[#f9fbf9]">
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <Avatar initials={user.initials} size="sm" color={rc.avatarColor} />
                          <span className="font-semibold text-[var(--ink)]">{user.name}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3 text-[var(--muted)]">{user.email}</td>
                      <td className="px-5 py-3">
                        <span
                          className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold capitalize"
                          style={{ backgroundColor: rc.bg, color: rc.text }}
                        >
                          {user.role}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-[var(--muted)]">{user.joinedAt}</td>
                      <td className="px-5 py-3">
                        <button className="rounded-lg border border-[var(--line)] px-3 py-1 text-[10px] font-semibold text-[var(--muted)] transition-colors hover:border-[var(--teal)] hover:text-[var(--teal)]">
                          View
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
