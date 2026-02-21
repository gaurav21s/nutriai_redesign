import { NextResponse } from "next/server";
import { clerkMiddleware } from "@clerk/nextjs/server";

const authDisabled = process.env.NEXT_PUBLIC_AUTH_DISABLED === "true";
const middleware = authDisabled ? () => NextResponse.next() : clerkMiddleware();

export default middleware;

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
