import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const isPublicRoute = createRouteMatcher([
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/api/webhooks(.*)",
  "/api/health(.*)",
]);

const isOnboardingRoute = createRouteMatcher(["/onboarding(.*)"]);

const STATE_TO_URL: Record<string, string> = {
  NOT_STARTED: "/onboarding?step=IDENTITY",
  IDENTITY: "/onboarding?step=IDENTITY",
  GOALS: "/onboarding?step=GOALS",
  EVIDENCE: "/onboarding?step=EVIDENCE",
  CONNECTIONS: "/onboarding?step=CONNECTIONS",
  BUILDING: "/onboarding?step=BUILDING",
};

export default clerkMiddleware(async (auth, req) => {
  if (isPublicRoute(req)) return;

  await auth.protect();

  // Already on onboarding — don't redirect in a loop
  if (isOnboardingRoute(req)) return;

  const { userId } = await auth();
  if (!userId) return;

  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const res = await fetch(`${apiUrl}/api/onboarding/state`, {
      headers: { "x-user-id": userId },
      signal: AbortSignal.timeout(5000),
    });

    if (res.ok) {
      const { state } = (await res.json()) as { state: string };
      if (state !== "READY") {
        const target = STATE_TO_URL[state] ?? "/onboarding?step=IDENTITY";
        return NextResponse.redirect(new URL(target, req.url));
      }
    }
  } catch {
    // Backend unreachable — fail open, let the user through
  }
});

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
    "/__clerk/:path*",
  ],
};
