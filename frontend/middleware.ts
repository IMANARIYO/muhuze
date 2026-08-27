import { NextRequest, NextResponse } from "next/server";

const ACCESS_COOKIE = "muhuze.accessToken";

export function middleware(request: NextRequest) {
  const hasSession = request.cookies.has(ACCESS_COOKIE);
  if (!hasSession) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("from", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  const role = request.cookies.get("muhuze.role")?.value;
  if (role !== "seller" && role !== "admin") {
    return NextResponse.redirect(new URL("/products", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
