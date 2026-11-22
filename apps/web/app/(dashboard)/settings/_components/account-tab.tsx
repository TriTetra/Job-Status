"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useMe } from "@/features/auth/use-me";
import { settingsApi, API_BASE } from "@/features/settings/api";
import type { GithubStatus, PortfolioStatus } from "@/features/onboarding/types";
import {
  crawlErrorMessage, crawlSummary, githubNotice, type Notice,
} from "@/features/onboarding/connect-messages";
import { Section, Row, UnderlineInput } from "./kit";
import { InvitesSection, PasswordRow } from "./access-section";

export function AccountTab() {
  const me = useMe();
  const [github, setGithub] = useState<GithubStatus | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioStatus | null>(null);
  const [urlOpen, setUrlOpen] = useState(false);
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [portfolioNotice, setPortfolioNotice] = useState<Notice | null>(null);
  const ghNotice = githubNotice(useSearchParams().get("github"));

  const refresh = () => {
    settingsApi
      .getGithubStatus()
      .then(setGithub)
      .catch(() => setGithub({ connected: false }));
    settingsApi
      .getPortfolioStatus()
      .then(setPortfolio)
      .catch(() => setPortfolio({ connected: false }));
  };

  useEffect(refresh, []);

  const connectGithub = () => {
    window.location.assign(`${API_BASE}/api/oauth/github/authorize?return_to=settings`);
  };

  const addPortfolio = async () => {
    if (!url) return;
    setBusy(true);
    setPortfolioNotice(null);
    try {
      const result = await settingsApi.crawlPortfolio(url);
      setUrlOpen(false);
      setUrl("");
      setPortfolioNotice({ tone: "ok", text: crawlSummary(result) });
      refresh();
    } catch (e) {
      setPortfolioNotice({ tone: "error", text: crawlErrorMessage(e) });
    } finally {
      setBusy(false);
    }
  };

  const textBtn = "text-xs underline underline-offset-4 transition-colors cursor-pointer";

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
        <Row label="GitHub" hint={ghNotice?.text ?? "Repository analysis raises skill confidence"}>
          {github?.connected ? (
            <span className="flex items-center gap-4">
              <span className="text-sm" style={{ color: "var(--success)" }}>
                @{github.username} · connected
              </span>
              <button
                className={textBtn}
                style={{ color: "var(--danger)" }}
                onClick={async () => {
                  await settingsApi.disconnectGithub();
                  refresh();
                }}
              >
                Disconnect
              </button>
            </span>
          ) : github?.available === false ? (
            <span className="text-xs" style={{ color: "var(--text-muted)" }} title="The site admin hasn't set up GitHub sign-in yet">
              Not set up
            </span>
          ) : (
            <button
              className={textBtn}
              style={{ color: "var(--accent)" }}
              onClick={connectGithub}
            >
              Connect
            </button>
          )}
        </Row>

        <Row label="Portfolio" hint={portfolioNotice?.text ?? "Crawled for projects and technologies"}>
          {portfolio?.connected ? (
            <span className="flex items-center gap-4 min-w-0">
              <span className="text-sm truncate" style={{ color: "var(--success)" }}>
                {portfolio.url} · connected
              </span>
              <button
                className={textBtn}
                style={{ color: "var(--danger)" }}
                onClick={async () => {
                  await settingsApi.disconnectPortfolio();
                  refresh();
                }}
              >
                Disconnect
              </button>
            </span>
          ) : urlOpen ? (
            <span className="flex items-center gap-3">
              <UnderlineInput
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://your-portfolio.com"
                onKeyDown={(e) => e.key === "Enter" && addPortfolio()}
              />
              <button
                className={textBtn}
                style={{ color: "var(--accent)" }}
                onClick={addPortfolio}
                disabled={busy}
              >
                {busy ? "Reading…" : "Add"}
              </button>
            </span>
          ) : (
            <button
              className={textBtn}
              style={{ color: "var(--accent)" }}
              onClick={() => setUrlOpen(true)}
            >
              Add URL
            </button>
          )}
        </Row>
      </Section>
    </div>
  );
}
