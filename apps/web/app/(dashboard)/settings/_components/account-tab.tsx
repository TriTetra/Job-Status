"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useMe } from "@/features/auth/use-me";
import { onboardingApi } from "@/features/onboarding/api";
import { githubNotice, NOTICE_COLOR } from "@/features/onboarding/connect-messages";
import { connectsByInput, SOURCE_INPUT, useSourceConnect } from "@/features/onboarding/use-source-connect";
import type { EvidenceSourceRow } from "@/features/onboarding/types";
import { Section, Row, UnderlineInput } from "./kit";
import { InvitesSection, PasswordRow } from "./access-section";

const textBtn = "text-xs underline underline-offset-4 transition-colors cursor-pointer disabled:opacity-40";

export function AccountTab() {
  const me = useMe();
  const [sources, setSources] = useState<EvidenceSourceRow[] | null>(null);
  const oauthNotice = githubNotice(useSearchParams().get("github"));

  const refresh = useCallback(() => {
    onboardingApi
      .getEvidenceSources()
      .then((d) => setSources(d.all.filter((s) => s.status === "available")))
      .catch(() => setSources([]));
  }, []);

  useEffect(refresh, [refresh]);

  const c = useSourceConnect(refresh, "settings");

  return (
    <div>
      <Section title="Account">
        <Row label="Name">
          <span className="text-sm" style={{ color: "var(--text-primary)" }}>
            {[me?.first_name, me?.last_name].filter(Boolean).join(" ") || "—"}
          </span>
        </Row>
        <Row label="Email" hint={me?.is_admin ? "Admin — you can invite people" : undefined}>
          <span className="text-sm" style={{ color: "var(--text-muted)" }}>
            {me?.email ?? "—"}
          </span>
        </Row>
        <PasswordRow />
      </Section>

      {me?.is_admin && <InvitesSection />}

      <Section title="Proof sources">
        {oauthNotice && (
          <p className="text-xs py-3" role="status" style={{ color: NOTICE_COLOR[oauthNotice.tone] }}>
            {oauthNotice.text}
          </p>
        )}
        {sources === null && (
          <p className="text-xs py-3" style={{ color: "var(--text-muted)" }}>Loading…</p>
        )}
        {sources?.map((s) => {
          const open = c.openId === s.id;
          const busy = c.busyId === s.id;
          const notice = c.notices[s.id];
          return (
            <Row key={s.id} label={s.label} hint={SOURCE_INPUT[s.id]?.hint}>
              {s.connected ? (
                <span className="flex items-center gap-4 min-w-0">
                  <span className="text-sm truncate" style={{ color: "var(--success)" }}>
                    {s.handle ? `${s.handle} · connected` : "connected"}
                  </span>
                  <button className={textBtn} style={{ color: "var(--danger)" }} disabled={busy} onClick={() => c.disconnect(s)}>
                    Disconnect
                  </button>
                </span>
              ) : open && connectsByInput(s) ? (
                <span className="flex items-center gap-3 min-w-0">
                  <UnderlineInput
                    autoFocus
                    value={c.value}
                    onChange={(e) => c.setValue(e.target.value)}
                    placeholder={SOURCE_INPUT[s.id]?.placeholder ?? "Username or profile link"}
                    aria-label={`${s.label} username or link`}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") c.submit(s);
                      if (e.key === "Escape") c.cancel();
                    }}
                  />
                  <button className={textBtn} style={{ color: "var(--accent)" }} onClick={() => c.submit(s)} disabled={busy || !c.value.trim()}>
                    {busy ? "Reading…" : "Add"}
                  </button>
                  <button className={textBtn} style={{ color: "var(--text-muted)" }} onClick={c.cancel}>
                    Cancel
                  </button>
                </span>
              ) : (
                <button className={textBtn} style={{ color: "var(--accent)" }} onClick={() => c.start(s)}>
                  Connect
                </button>
              )}
              {notice && (
                <p className="text-xs mt-1.5" role={notice.tone === "error" ? "alert" : "status"} style={{ color: NOTICE_COLOR[notice.tone] }}>
                  {notice.text}
                </p>
              )}
            </Row>
          );
        })}
      </Section>
    </div>
  );
}
