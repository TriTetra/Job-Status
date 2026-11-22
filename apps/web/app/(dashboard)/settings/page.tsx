import { redirect } from "next/navigation";
import { legacyTab, SETTINGS_PARAM } from "@/features/settings/sections";

type Params = Record<string, string | string[] | undefined>;
const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v);

/** Settings lives in a dialog over the app; old /settings?tab=… links open it on the Briefing. */
export default async function SettingsPage({ searchParams }: { searchParams: Promise<Params> }) {
  const sp = await searchParams;
  const q = new URLSearchParams({ [SETTINGS_PARAM]: legacyTab(one(sp.tab)) });
  const github = one(sp.github);
  if (github) q.set("github", github);
  redirect(`/briefing?${q}`);
}
