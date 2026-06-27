import { BACKEND_BASE } from "@/lib/config";

export const dynamic = "force-dynamic";

// Proxy voicemail audio playback from the backend (uploaded voicemails only).
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const res = await fetch(`${BACKEND_BASE}/audio/${id}`, { cache: "no-store" });
  if (!res.ok) return new Response("audio not found", { status: res.status });
  return new Response(res.body, {
    status: 200,
    headers: { "Content-Type": res.headers.get("Content-Type") ?? "audio/wav" },
  });
}
