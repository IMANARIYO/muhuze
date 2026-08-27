import { Card, CardContent, CardHeader, CardTitle } from "@/app/_components/ui/card";
import { Button } from "@/app/_components/ui/button";
import { Avatar } from "@/app/_components/ui/avatar";
import { Input } from "@/app/_components/ui/input";
import { Badge } from "@/app/_components/ui/badge";
import { Mail, ShoppingBag } from "lucide-react";

export default function ProfilePage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-[var(--ink)]">Profile</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Manage your account information and preferences.
        </p>
      </div>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-5">
            <Avatar initials="AM" size="lg" color="#d7896d" />
            <div>
              <h2 className="text-lg font-bold text-[var(--ink)]">Amina M.</h2>
              <p className="flex items-center gap-1.5 text-xs text-[var(--muted)]">
                <Mail size={12} /> amina@example.com
              </p>
              <div className="mt-1.5 flex items-center gap-2">
                <Badge variant="secondary">Client</Badge>
                <span className="flex items-center gap-1 text-[10px] text-[#9ba49e]">
                  <ShoppingBag size={10} /> 3 orders placed
                </span>
              </div>
            </div>
            <Button variant="outline" size="sm" className="ml-auto">
              Edit photo
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Personal Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-[var(--ink)]">Full name</label>
              <Input defaultValue="Amina M." />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-[var(--ink)]">Email</label>
              <Input defaultValue="amina@example.com" type="email" />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-[var(--ink)]">Phone</label>
              <Input placeholder="+254 700 000 000" type="tel" />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-[var(--ink)]">Location</label>
              <Input defaultValue="Nairobi, Kenya" />
            </div>
          </div>
          <Button>Save changes</Button>
        </CardContent>
      </Card>
    </div>
  );
}
