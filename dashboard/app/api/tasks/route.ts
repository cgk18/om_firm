import { NextResponse } from "next/server";
import { BACKEND_BASE } from "@/lib/config";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_BASE}/tasks`, { cache: "no-store" });
    const body = await res.json();
    return NextResponse.json(body, { status: res.status });
  } catch {
    return NextResponse.json({ detail: "backend unreachable" }, { status: 502 });
  }
}
