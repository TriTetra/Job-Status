import {
  Compass,
  Building2,
  TrendingUp,
  Database,
  GraduationCap,
  FileText,
  ClipboardList,
  BarChart3,
  Clock,
  Settings,
  Sparkles,
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
      { label: "Briefing", href: "/briefing", icon: Sparkles, badge: "4" },
    ],
  },
  {
    title: "DISCOVER",
    items: [
      { label: "Opportunities", href: "/inbox", icon: Compass, badge: 17 },
      { label: "Companies", href: "/companies", icon: Building2 },
      { label: "Market", href: "/market", icon: TrendingUp },
    ],
  },
  {
    title: "BUILD",
    items: [
      { label: "Evidence", href: "/evidence", icon: Database },
      { label: "Learning", href: "/learning", icon: GraduationCap },
      { label: "Resume", href: "/resume", icon: FileText },
    ],
  },
  {
    title: "MANAGE",
    items: [
      { label: "Applications", href: "/applications", icon: ClipboardList, badge: 3 },
      { label: "Analytics", href: "/analytics", icon: BarChart3 },
      { label: "Timeline", href: "/timeline", icon: Clock, comingSoon: true },
    ],
  },
  {
    title: "SYSTEM",
    items: [
      { label: "Settings", href: "/settings", icon: Settings },
    ],
  },
];

export const ALL_NAV_ITEMS: NavItem[] = NAV_GROUPS.flatMap((g) => g.items);
