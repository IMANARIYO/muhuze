"use client";

import { useState } from "react";
import {
  ArrowUpRight,
  Bell,
  BriefcaseBusiness,
  ChevronDown,
  CircleHelp,
  Compass,
  FileText,
  LayoutDashboard,
  MapPin,
  Menu,
  MessageCircle,
  Plus,
  Search,
  Settings,
  Sparkles,
  Users,
  X,
} from "lucide-react";

import { Badge, Button, Card } from "./ui";

const navItems = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Opportunities", icon: BriefcaseBusiness, count: "12" },
  { label: "Connections", icon: Users, count: "4" },
  { label: "Messages", icon: MessageCircle, count: "2" },
];

const opportunities = [
  { title: "East Africa Trade Forum", type: "Event", location: "Nairobi, Kenya", date: "Sep 18", color: "coral" },
  { title: "Sustainable Cities Fund", type: "Funding", location: "Global", date: "Sep 24", color: "blue" },
  { title: "Makers in Motion", type: "Community", location: "Kigali, Rwanda", date: "Oct 02", color: "yellow" },
];

const regions = [
  { name: "East Africa", value: 68, color: "var(--teal)" },
  { name: "West Africa", value: 42, color: "var(--coral)" },
  { name: "Europe", value: 31, color: "var(--sky)" },
];

export function MuhuzeWorkspace() {
  const [activeNav, setActiveNav] = useState("Overview");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [showComposer, setShowComposer] = useState(false);
  const [role, setRole] = useState("Explorer");

  const filteredOpportunities = opportunities.filter((opportunity) =>
    `${opportunity.title} ${opportunity.type} ${opportunity.location}`.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <main className="app-frame">
      <aside className={`sidebar ${mobileNavOpen ? "sidebar-open" : ""}`}>
        <div className="sidebar-top">
          <div className="brand-mark">M</div>
          <div className="brand-wordmark">muhuze<span>.</span></div>
          <Button variant="ghost" className="mobile-close" aria-label="Close menu" onClick={() => setMobileNavOpen(false)}><X size={18} /></Button>
        </div>

        <button className="profile-switcher" onClick={() => setRole(role === "Explorer" ? "Builder" : "Explorer")} aria-label="Switch profile role">
          <div className="avatar avatar-small">AM</div>
          <div className="profile-copy"><strong>Amina M.</strong><span>{role}</span></div>
          <ChevronDown size={15} />
        </button>

        <div className="nav-label">Workspace</div>
        <nav className="main-nav" aria-label="Main navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            return <button key={item.label} className={`nav-item ${activeNav === item.label ? "nav-item-active" : ""}`} onClick={() => { setActiveNav(item.label); setMobileNavOpen(false); }}><Icon size={17} /><span>{item.label}</span>{item.count && <em>{item.count}</em>}</button>;
          })}
        </nav>

        <div className="nav-label nav-label-spaced">Manage</div>
        <nav className="main-nav" aria-label="Manage navigation">
          <button className="nav-item" onClick={() => setActiveNav("My profile")}><Compass size={17} /><span>My profile</span></button>
          <button className="nav-item" onClick={() => setActiveNav("Saved items")}><FileText size={17} /><span>Saved items</span></button>
          <button className="nav-item" onClick={() => setActiveNav("Settings")}><Settings size={17} /><span>Settings</span></button>
        </nav>

        <div className="sidebar-footer"><div className="help-icon"><CircleHelp size={16} /></div><div><strong>Need a hand?</strong><span>Visit our help center</span></div><ArrowUpRight size={15} /></div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <Button variant="ghost" className="mobile-menu" aria-label="Open menu" onClick={() => setMobileNavOpen(true)}><Menu size={20} /></Button>
          <div className="breadcrumbs"><span>Workspace</span><b>/</b><strong>{activeNav}</strong></div>
          <div className="topbar-actions">
            <label className="search-box"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search workspace" aria-label="Search workspace" /><kbd>⌘ K</kbd></label>
            <button className="icon-button notification" aria-label="Notifications"><Bell size={18} /><i /></button>
            <div className="avatar avatar-top">AM</div>
          </div>
        </header>

        <div className="content">
          <section className="welcome-row"><div><p className="eyebrow">Wednesday, August 26, 2026</p><h1>Good morning, Amina <span>↗</span></h1><p className="lede">Your global network has been busy while you were away.</p></div><Button onClick={() => setShowComposer(true)}><Plus size={17} /> Share an opportunity</Button></section>

          <section className="metrics-grid" aria-label="Workspace summary">
            <Card className="metric-card metric-featured"><div className="metric-icon"><Sparkles size={18} /></div><span>Profile reach</span><strong>2,840</strong><small><b>+18.4%</b> from last month</small><div className="sparkline"><i /><i /><i /><i /><i /><i /><i /></div></Card>
            <Card className="metric-card"><div className="metric-heading"><span>New connections</span><Users size={17} /></div><strong>24</strong><small><b>+6</b> this week</small><div className="mini-avatars"><span>JO</span><span>SN</span><span>IK</span><span>+21</span></div></Card>
            <Card className="metric-card"><div className="metric-heading"><span>Saved opportunities</span><FileText size={17} /></div><strong>08</strong><small><b>3 closing soon</b></small><div className="progress-line"><i /></div></Card>
          </section>

          <div className="section-grid">
            <Card className="opportunity-card"><div className="section-heading"><div><p className="eyebrow">Curated for you</p><h2>Latest opportunities</h2></div><button className="text-button" onClick={() => setActiveNav("Opportunities")}>View all <ArrowUpRight size={15} /></button></div><div className="opportunity-list">{filteredOpportunities.map((opportunity) => <button className="opportunity-row" key={opportunity.title}><div className={`opportunity-badge ${opportunity.color}`}><BriefcaseBusiness size={18} /></div><div className="opportunity-info"><strong>{opportunity.title}</strong><span>{opportunity.type} <i /> <MapPin size={12} /> {opportunity.location}</span></div><Badge>{opportunity.date}</Badge><ArrowUpRight className="row-arrow" size={16} /></button>)}{filteredOpportunities.length === 0 && <p className="empty-state">No opportunities match your search.</p>}</div></Card>

            <Card className="network-card"><div className="section-heading"><div><p className="eyebrow">Your network</p><h2>Where you connect</h2></div><button className="icon-button" aria-label="Open network"><ArrowUpRight size={16} /></button></div><div className="network-visual"><div className="network-ring ring-one" /><div className="network-ring ring-two" /><div className="network-core"><strong>141</strong><span>connections</span></div><div className="map-pin pin-one"><MapPin size={15} /></div><div className="map-pin pin-two"><MapPin size={15} /></div><div className="map-pin pin-three"><MapPin size={15} /></div></div><div className="region-list">{regions.map((region) => <div key={region.name}><span><i style={{ backgroundColor: region.color }} />{region.name}</span><strong>{region.value}</strong></div>)}</div></Card>
          </div>

          <Card className="prompt-card"><div className="prompt-shape"><span>✦</span></div><div><p className="eyebrow">Make your mark</p><h2>What are you building next?</h2><p>Tell the network what you&apos;re working on and find the people who can move it forward.</p></div><Button variant="outline" onClick={() => setShowComposer(true)}>Start a post <ArrowUpRight size={16} /></Button></Card>
        </div>
      </section>

      {showComposer && <div className="modal-backdrop" role="presentation" onClick={() => setShowComposer(false)}><div className="composer-modal" role="dialog" aria-modal="true" aria-labelledby="composer-title" onClick={(event) => event.stopPropagation()}><div className="modal-header"><div><p className="eyebrow">Share with your network</p><h2 id="composer-title">Create a post</h2></div><button className="icon-button" onClick={() => setShowComposer(false)} aria-label="Close dialog"><X size={18} /></button></div><textarea placeholder="Share an update, opportunity, or question..." autoFocus /><div className="modal-footer"><span>Visible to your connections</span><Button onClick={() => setShowComposer(false)}>Publish post <ArrowUpRight size={16} /></Button></div></div></div>}
    </main>
  );
}
