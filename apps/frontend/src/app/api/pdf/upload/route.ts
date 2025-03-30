import { getServerSession } from 'next-auth/next';
import { NextRequest, NextResponse } from 'next/server';
import { authOptions } from '@/app/api/auth/[...nextauth]/options';

export async function POST(request: NextRequest) {
  try {
    // Check if user is authenticated
    const session = await getServerSession(authOptions);

    if (!session?.user) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    // Get form data
    const formData = await request.formData();

    // Check if file exists
    const file = formData.get('file') as File;
    if (!file) {
      return NextResponse.json({ error: 'File is required' }, { status: 400 });
    }

    // Forward request to backend API
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    // Create new FormData to send to backend
    const backendFormData = new FormData();
    backendFormData.append('file', file);

    // Add optional fields if they exist
    const description = formData.get('description');
    if (description) {
      backendFormData.append('description', description.toString());
    }

    const response = await fetch(`${backendUrl}/api/pdf/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${session.accessToken}`,
      },
      body: backendFormData,
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || 'Failed to upload PDF' },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Error uploading PDF:', error);

    return NextResponse.json(
      {
        detail: 'Error uploading PDF',
        error: error.message,
      },
      { status: 500 }
    );
  }
}
