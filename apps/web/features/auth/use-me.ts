"use client";

import { useEffect, useState } from "react";

import { authApi } from "./api";
import type { Me } from "./types";

// One request per page load, shared by every component that asks
let mePromise: Promise<Me | null> | null = null;

function loadMe(): Promise<Me | null> {
  mePromise ??= authApi.me().catch(() => null);
  return mePromise;
}

/** The signed-in user (null while loading or if the session ended). */
export function useMe(): Me | null {
  const [me, setMe] = useState<Me | null>(null);
  useEffect(() => {
    let alive = true;
    loadMe().then((m) => {
      if (alive) setMe(m);
    });
    return () => {
      alive = false;
    };
  }, []);
  return me;
}

/** End the session on the server, forget the cached user, go to sign-in. */
export async function signOut(): Promise<void> {
  try {
    await authApi.logout();
  } finally {
    mePromise = null;
    window.location.assign("/sign-in");
  }
}
