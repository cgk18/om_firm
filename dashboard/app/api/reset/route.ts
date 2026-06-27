import { NextResponse } from "next/server";
import { BACKEND_BASE } from "@/lib/config";

export const dynamic = "force-dynamic";

export async function POST() {
  try {
    const res = await fetch(`${BACKEND_BASE}/reset`, {
      method: "POST",
      cache: "no-store",
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ detail: "backend unreachable" }, { status: 502 });
  }
}
