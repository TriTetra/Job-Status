"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import { telegramApi, type TelegramStatus } from "@/features/settings/telegram";
import { CheckRow, Row, Section } from "./kit";

const textBtn = "text-xs underline underline-offset-4 transition-colors cursor-pointer disabled:opacity-40";
const WAIT_MS = 3 * 60_000;

/** Telegram: connect with one tap in the bot, choose what to hear about, test it. */
export function TelegramSection() {
  const [st, setSt] = useState<TelegramStatus | null>(null);
  const [waiting, setWaiting] = useState(false);
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    try {
      const s = await telegramApi.status();
      setSt(s);
      return s;
    } catch {
      setSt(null);
      return null;
    }
  }, []);

  useEffect(() => {
    telegramApi.status().then(setSt).catch(() => setSt(null));
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, [load]);

  // After opening the bot: check every few seconds until Start was pressed
  const watch = () => {
    if (timer.current) clearInterval(timer.current);
    const until = Date.now() + WAIT_MS;
    setWaiting(true);
    timer.current = setInterval(async () => {
      const s = await load();
      if (s?.connected || Date.now() > until) {
        if (timer.current) clearInterval(timer.current);
        setWaiting(false);
        if (s?.connected) setNote({ ok: true, text: "Connected. You'll hear from Aplio in Telegram." });
      }
    }, 3000);
  };

  const connect = async () => {
    setBusy(true);
    setNote(null);
    // Open the tab now (inside the click), point it at the bot once the link exists
    const tab = window.open("about:blank", "_blank");
    try {
      const { url } = await telegramApi.link();
      if (tab) tab.location.href = url;
      else window.location.assign(url);
      watch();
    } catch {
      tab?.close();
      setNote({ ok: false, text: "Couldn't create the link. Try again in a moment." });
    } finally {
      setBusy(false);
    }
  };

  const togglePref = async (key: "matches" | "reminders" | "report", value: boolean) => {
    if (!st) return;
    setSt({ ...st, prefs: { ...st.prefs, [key]: value } });
    try {
      const { prefs } = await telegramApi.prefs({ [key]: value });
      setSt((s) => (s ? { ...s, prefs } : s));
    } catch {
      load();
    }
  };

  const test = async () => {
    setBusy(true);
    try {
      await telegramApi.test();
      setNote({ ok: true, text: "Sent. Check Telegram." });
    } catch {
      setNote({ ok: false, text: "Couldn't reach your chat. If you blocked the bot, connect again." });
    } finally {
      setBusy(false);
    }
  };

  const disconnect = async () => {
    setBusy(true);
    try {
      await telegramApi.disconnect();
      setNote(null);
      await load();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Section title="Notifications">
      <Row label="Telegram" hint="New strong matches and reminders for applications that wait too long">
        {st === null ? (
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>Loading…</span>
        ) : !st.available ? (
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            Not set up on this server yet (the admin adds a bot token).
          </span>
        ) : st.connected ? (
          <span className="flex flex-wrap items-center gap-x-4 gap-y-2 min-w-0">
            <span className="inline-flex items-center gap-1.5 text-sm" style={{ color: "var(--success)" }}>
              <Send className="h-3.5 w-3.5" /> {st.username ? `@${st.username}` : "Connected"}
            </span>
            <button className={textBtn} style={{ color: "var(--accent)" }} disabled={busy} onClick={test}>Send a test</button>
            <button className={textBtn} style={{ color: "var(--danger)" }} disabled={busy} onClick={disconnect}>Disconnect</button>
          </span>
        ) : waiting ? (
          <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
            Press <b>Start</b> in Telegram{st.bot ? <> (@{st.bot})</> : null}. This updates by itself.{" "}
            <button className={textBtn} style={{ color: "var(--accent)" }} onClick={connect} disabled={busy}>Open again</button>
          </span>
        ) : (
          <button onClick={connect} disabled={busy}
                  className="inline-flex items-center gap-2 h-8 px-3 rounded-lg text-sm font-semibold disabled:opacity-50"
                  style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>
            <Send className="h-3.5 w-3.5" /> Connect Telegram
          </button>
        )}
        {note && (
          <p className="text-xs mt-1.5" role={note.ok ? "status" : "alert"} style={{ color: note.ok ? "var(--success)" : "var(--danger)" }}>
            {note.text}
          </p>
        )}
      </Row>
      {st?.connected && (
        <>
          <CheckRow checked={st.prefs.matches} onChange={(v) => togglePref("matches", v)}
                    label="New strong matches" hint="After each refresh (about every 6 hours), only roles you haven't been told about" />
          <CheckRow checked={st.prefs.reminders} onChange={(v) => togglePref("reminders", v)}
                    label="Follow-up reminders" hint="An application with no answer for two weeks, once" />
          <CheckRow checked={st.prefs.report ?? true} onChange={(v) => togglePref("report", v)}
                    label="Daily report" hint="Once a day: what's ready to apply, where your applications stand, what to learn next" />
        </>
      )}
    </Section>
  );
}
