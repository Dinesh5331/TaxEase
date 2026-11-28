import { NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  try {
    // The backend validates the fields; forward the multipart body as received.
    const res = await fetch(`${BACKEND}/api/itr/analyze`, {
      method: "POST",
      headers: { "ngrok-skip-browser-warning": "true" },
      body: await request.formData(),
    });
    const data = await res.json().catch(() => ({ detail: "Unknown backend error" }));
    if (!res.ok) {
      const error = typeof data.detail === "string" ? data.detail : "Could not analyse the documents";
      return NextResponse.json({ error }, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (error) {
    console.error("[/api/itr/analyze] error:", error);
    return NextResponse.json({ error: "Failed to reach TaxAssist backend" }, { status: 503 });
  }
}
