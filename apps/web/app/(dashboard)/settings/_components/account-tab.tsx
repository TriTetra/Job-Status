"use client";

import { useEffect, useState } from "react";
import { useMe } from "@/features/auth/use-me";
import { settingsApi, API_BASE } from "@/features/settings/api";
import type { GithubStatus, PortfolioStatus } from "@/features/onboarding/types";
import { Section, Row, UnderlineInput } from "./kit";

export function AccountTab() {
  const me = useMe();
  const [github, setGithub] = useState<GithubStatus | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioStatus | null>(null);
  const [urlOpen, setUrlOpen] = useState(false);
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);

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
    window.location.assign(`${API_BASE}/api/oauth/github/authorize`);
  };

  const addPortfolio = async () => {
    if (!url) return;
    setBusy(true);
    try {
      await settingsApi.crawlPortfolio(url);
      setUrlOpen(false);
      setUrl("");
      refresh();
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
        <Row label="Email" hint="Change it with: career-os user …">
          <span className="text-sm" style={{ color: "var(--text-muted)" }}>
            {me?.email ?? "—"}
          </span>
        </Row>
      </Section>

      <Section title="Proof sources">
        <Row label="GitHub" hint="Repository analysis raises skill confidence">
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

        <Row label="Portfolio" hint="Crawled for projects and technologies">
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
                {busy ? "Crawling…" : "Add"}
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
