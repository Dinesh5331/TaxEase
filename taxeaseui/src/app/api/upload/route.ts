import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get('file');

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    // Mock processing delay
    await new Promise(resolve => setTimeout(resolve, 1500));

    return NextResponse.json({ 
      success: true, 
      message: "File uploaded successfully",
      fileName: (file as File).name,
      status: "processing"
    });
  } catch (error) {
    return NextResponse.json({ error: "Failed to upload file" }, { status: 500 });
  }
}
