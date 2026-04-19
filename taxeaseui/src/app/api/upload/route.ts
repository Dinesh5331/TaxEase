import { NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get("file");
    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }
    const backendForm = new FormData();
    backendForm.append("file", file as Blob, (file as File).name);
    const res = await fetch(`${BACKEND}/api/upload`, {
      method: "POST",
      headers: {
        "ngrok-skip-browser-warning": "true",
      },
      body: backendForm,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Unknown backend error" }));
      return NextResponse.json(
        { error: err.detail ?? "Failed to process file" },
        { status: res.status }
      );
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("[/api/upload] error:", error);
    return NextResponse.json(
      { error: "Failed to reach TaxAssist backend. Is the server running?" },
      { status: 503 }
    );
  }
}