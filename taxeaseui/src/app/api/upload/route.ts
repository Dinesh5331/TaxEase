import { NextResponse } from "next/server";

const BACKEND =
  process.env.BACKEND_URL ??
  process.env.NEXT_PUBLIC_BACKEND_URL ??
  "http://localhost:8000";

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get("file");

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    // Forward the file to the FastAPI backend as multipart
    const backendForm = new FormData();
    backendForm.append("file", file as Blob, (file as File).name);

    const res = await fetch(`${BACKEND}/upload`, {
      method: "POST",
      body: backendForm,
      // Note: do NOT set Content-Type header — fetch sets it automatically with boundary
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

