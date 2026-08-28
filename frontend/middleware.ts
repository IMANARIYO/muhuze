import { NextRequest, NextResponse } from "next/server";

const ACCESS_COOKIE = "muhuze.accessToken";

export function middleware(request: NextRequest) {
  const hasSession = request.cookies.has(ACCESS_COOKIE);
  if (!hasSession) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("from", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  // All authenticated roles (client/seller/admin) can access the dashboard.
  // Role-based content filtering happens inside the dashboard components.
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
