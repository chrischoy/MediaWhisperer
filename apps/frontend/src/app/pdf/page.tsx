'use client';

import { useState } from 'react';
import Link from 'next/link';
import PDFList from '@/components/pdf/PDFList';
import PDFImport from '@/components/pdf/PDFImport';

export default function PDFPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleSuccess = () => {
    // Increment the key to force the PDFList to re-fetch
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="container mx-auto p-6 max-w-5xl">
      <div className="mb-6">
        <Link href="/dashboard" className="text-blue-500 hover:underline flex items-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 mr-1"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z"
              clipRule="evenodd"
            />
          </svg>
          Back to Dashboard
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Add PDF</h2>
            <PDFImport onSuccess={handleSuccess} />
          </div>
        </div>

        <div className="lg:col-span-2">
          <h1 className="text-2xl font-bold mb-6">Your PDFs</h1>
          <PDFList key={refreshKey} />
        </div>
      </div>
    </div>
  );
}
