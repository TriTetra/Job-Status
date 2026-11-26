#!/bin/sh
# CareerOS worker: the scheduled job runs, each in its own short-lived process.
#
# `career-os jobs run` does whatever is due: the full refresh every JOB_SYNC_INTERVAL_HOURS,
# otherwise a tick (due boards, new matches to Telegram, hourly mailboxes). When it ran is kept
# in the database, so a restart or redeploy doesn't repeat a full refresh. When the process
# exits, all the memory it grew into goes back to the system: the web API never holds it.
set -u

TICK="${JOB_TICK_MINUTES:-15}"
TICK="${TICK%.*}"                      # whole minutes
case "$TICK" in ''|*[!0-9]*) TICK=15 ;; esac
[ "$TICK" -ge 1 ] || TICK=15

sleep "${WORKER_START_DELAY:-60}"      # the API applies migrations on start
while true; do
  career-os jobs run || echo "worker: run exited with $?" >&2
  sleep $((TICK * 60))
done
