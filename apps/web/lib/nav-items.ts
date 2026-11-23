import {
  Compass,
  Building2,
  TrendingUp,
  Database,
  GraduationCap,
  FileText,
  ClipboardList,
  BarChart3,
  Sparkles,
  Search,
  Send,
} from "lucide-react";
import { type LucideIcon } from "lucide-react";

export type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
  badge?: string | number;
  disabled?: boolean;
  comingSoon?: boolean;
};

export type NavGroup = {
  title: string;
  items: NavItem[];
};

export const NAV_GROUPS: NavGroup[] = [
  {
    title: "TODAY",
    items: [
      { label: "Briefing", href: "/briefing", icon: Sparkles },
    ],
  },
  {
    title: "DISCOVER",
    items: [
      { label: "Opportunities", href: "/inbox", icon: Compass },
      { label: "Search", href: "/search", icon: Search },
      { label: "Companies", href: "/companies", icon: Building2 },
      { label: "Market", href: "/market", icon: TrendingUp },
    ],
  },
  {
    title: "BUILD",
    items: [
      { label: "Evidence", href: "/evidence", icon: Database, comingSoon: true },
      { label: "Learning", href: "/learning", icon: GraduationCap, comingSoon: true },
      { label: "Resume", href: "/resume", icon: FileText, comingSoon: true },
    ],
  },
  {
    title: "MANAGE",
    items: [
      { label: "Ready to apply", href: "/apply", icon: Send },
      { label: "Applications", href: "/applications", icon: ClipboardList },
      { label: "Analytics", href: "/analytics", icon: BarChart3 },
    ],
  },
];

export const ALL_NAV_ITEMS: NavItem[] = NAV_GROUPS.flatMap((g) => g.items);
