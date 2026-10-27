import { NextResponse, type NextRequest } from "next/server";

// Must match careeros/identity/auth/sessions.py COOKIE_NAME
const SESSION_COOKIE = "careeros_session";
const PUBLIC_PATHS = ["/sign-in"];

/**
 * Signed-out visitors only ever see /sign-in. This is a fast first gate — the
 * API validates the session on every request, so a stale or forged cookie
 * still gets nothing (the dashboard then sends the user back here).
 */
export function proxy(req: NextRequest) {
  const { pathname, search } = req.nextUrl;
  if (PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    return NextResponse.next();
  }
  if (!req.cookies.has(SESSION_COOKIE)) {
    const url = new URL("/sign-in", req.url);
    if (pathname !== "/") url.searchParams.set("next", `${pathname}${search}`);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  // Pages only: /api/* is forwarded to the backend (which does its own auth), static files are skipped
  matcher: [
    "/((?!api/|_next/|[^?]*\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
  ],
};
