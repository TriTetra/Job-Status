"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/api/client";
import { onboardingApi } from "./api";
import { crawlErrorMessage, crawlSummary, type Notice } from "./connect-messages";
import type { EvidenceSourceRow } from "./types";

/** What to type for each source that connects by username / link. */
export const SOURCE_INPUT: Record<string, { placeholder: string; hint: string }> = {
  github: { placeholder: "github.com/username", hint: "Public repositories: languages, topics and projects" },
  gitlab: { placeholder: "gitlab.com/username", hint: "Public projects and their languages" },
  stackoverflow: { placeholder: "stackoverflow.com/users/12345/your-name", hint: "Your top tags and reputation" },
  orcid: { placeholder: "0000-0002-1825-0097", hint: "Publications and grants on your ORCID record" },
  medium: { placeholder: "medium.com/@username", hint: "Your recent posts and their topics" },
  substack: { placeholder: "yourname.substack.com", hint: "Your recent posts and their topics" },
  portfolio: { placeholder: "https://your-portfolio.com", hint: "Projects and technologies on your site" },
};

/** True when the row connects through an inline input (profile link or portfolio URL). */
export const connectsByInput = (s: EvidenceSourceRow) => s.connect_kind === "profile" || s.connect_kind === "url";

/**
 * Connect / disconnect logic shared by onboarding and Settings: one source's input
 * open at a time, a result or error sentence per source.
 */
export function useSourceConnect(onChanged: () => void, returnTo: "onboarding" | "settings") {
  const [openId, setOpenId] = useState<string | null>(null);
  const [value, setValue] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [notices, setNotices] = useState<Record<string, Notice>>({});

  const note = (id: string, n: Notice | null) =>
    setNotices((prev) => {
      const next = { ...prev };
      if (n) next[id] = n;
      else delete next[id];
      return next;
    });

  const start = (s: EvidenceSourceRow) => {
    if (s.connect_kind === "oauth" && s.oauth_provider) {
      window.location.assign(`${API_BASE}/api/oauth/${s.oauth_provider}/authorize?return_to=${returnTo}`);
      return;
    }
    setOpenId(s.id);
    setValue("");
    note(s.id, null);
  };

  const submit = async (s: EvidenceSourceRow) => {
    if (!value.trim()) return;
    setBusyId(s.id);
    note(s.id, null);
    try {
      const text =
        s.connect_kind === "url"
          ? crawlSummary(await onboardingApi.crawlPortfolio(value.trim()))
          : (await onboardingApi.connectProfile(s.id, value.trim())).summary;
      note(s.id, { tone: "ok", text });
      setOpenId(null);
      setValue("");
      onChanged();
    } catch (e) {
      note(s.id, { tone: "error", text: crawlErrorMessage(e) });
    } finally {
      setBusyId(null);
    }
  };

  const disconnect = async (s: EvidenceSourceRow) => {
    setBusyId(s.id);
    try {
      if (s.connect_kind === "url") await onboardingApi.disconnectPortfolio();
      else await onboardingApi.disconnectProfile(s.id);
      note(s.id, null);
      onChanged();
    } catch (e) {
      note(s.id, { tone: "error", text: crawlErrorMessage(e) });
    } finally {
      setBusyId(null);
    }
  };

  return {
    openId, value, setValue, busyId, notices,
    start, submit, disconnect, cancel: () => setOpenId(null),
  };
}
