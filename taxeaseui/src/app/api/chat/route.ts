import { NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL;

if (!BACKEND) {
  throw new Error("NEXT_PUBLIC_API_URL is not set");
}

export async function POST(request: Request) {
  try {
    const body = await request.json();

    if (!body.query || typeof body.query !== "string" || !body.query.trim()) {
      return NextResponse.json({ error: "Query is required" }, { status: 400 });
    }

    const res = await fetch(`${BACKEND}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true",
      },
      body: JSON.stringify({
        query: body.query.trim(),
        debug: body.debug ?? false,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Unknown backend error",
      }));

      return NextResponse.json(
        { error: err.detail ?? "Backend error" },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("[/api/chat] error:", error);
    return NextResponse.json(
      { error: "Failed to reach TaxAssist backend" },
      { status: 503 }
    );
  }
}