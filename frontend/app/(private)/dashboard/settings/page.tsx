import { Card, CardContent, CardHeader, CardTitle } from "@/app/_components/ui/card";
import { Button } from "@/app/_components/ui/button";
import { Input } from "@/app/_components/ui/input";
import { Bell, CreditCard, Lock, Palette } from "lucide-react";

const sections = [
  { icon: Bell,       title: "Notifications",    desc: "Manage order updates, payment alerts, and payout notifications." },
  { icon: Lock,       title: "Security",          desc: "Update your password and enable two-factor authentication." },
  { icon: CreditCard, title: "Payment Methods",   desc: "Add or update your payment and payout account details." },
  { icon: Palette,    title: "Appearance",        desc: "Customize how Muhuze looks on your device." },
];

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-[var(--ink)]">Settings</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Manage your account preferences and configuration.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-[var(--ink)]">Display name</label>
              <Input defaultValue="Amina M." />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-[var(--ink)]">Email</label>
              <Input defaultValue="amina@example.com" type="email" />
            </div>
          </div>
          <Button>Save</Button>
        </CardContent>
      </Card>

      <div className="space-y-3">
        {sections.map((s) => {
          const Icon = s.icon;
          return (
            <Card key={s.title} className="transition-shadow hover:shadow-md">
              <CardContent className="flex items-center gap-4 p-5">
                <div className="grid h-10 w-10 place-items-center rounded-lg bg-[#e8f3ed] text-[var(--teal)]">
                  <Icon size={18} />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-bold text-[var(--ink)]">{s.title}</p>
                  <p className="text-xs text-[var(--muted)]">{s.desc}</p>
                </div>
                <Button variant="outline" size="sm">Configure</Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
