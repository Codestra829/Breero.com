import { NextRequest, NextResponse } from "next/server";
import { forwardedHeaders, proxyApiRequest } from "@/lib/server-api";

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "A valid JSON request is required." }, { status: 400 });
  }

  return proxyApiRequest(request, "/addresses/validate", {
    method: "POST",
    headers: forwardedHeaders(request),
    body: JSON.stringify(body),
  });
}
