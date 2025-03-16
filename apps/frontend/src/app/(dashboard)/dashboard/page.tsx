import { Metadata } from 'next';
import { requireAuth } from '@/lib/auth';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Dashboard | MediaWhisperer',
  description: 'MediaWhisperer Dashboard',
};

export default async function DashboardPage() {
  const user = await requireAuth();

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Welcome, {user.name}!</h1>

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Get Started</h2>
        <p className="mb-4">
          MediaWhisperer helps you understand and interact with your media files. Upload a PDF or
          paste a YouTube URL to get started.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          <div className="border rounded-lg p-4 hover:bg-gray-50 transition">
            <h3 className="font-medium mb-2">Process PDF Files</h3>
            <p className="text-gray-600 text-sm mb-3">
              Upload a PDF file to analyze its content, generate summaries, and chat with it.
            </p>
            <Link
              href="/pdf"
              className="inline-block bg-blue-600 text-white px-4 py-2 rounded text-sm"
            >
              Upload PDF
            </Link>
          </div>

          <div className="border rounded-lg p-4 hover:bg-gray-50 transition">
            <h3 className="font-medium mb-2">Process YouTube Videos</h3>
            <p className="text-gray-600 text-sm mb-3">
              Paste a YouTube URL to transcribe the video, analyze its content, and chat with it.
            </p>
            <Link
              href="/youtube"
              className="inline-block bg-blue-600 text-white px-4 py-2 rounded text-sm"
            >
              Process Video
            </Link>
          </div>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Terminal Access</h2>
        <p className="mb-4">Access the interactive terminal for advanced operations.</p>
        <Link
          href="/terminal"
          className="inline-block bg-gray-800 text-white px-4 py-2 rounded text-sm"
        >
          Open Terminal
        </Link>
      </div>
    </div>
  );
}
