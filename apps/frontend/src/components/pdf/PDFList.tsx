'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { pdfService, PDFDocument } from '@/services';

const PDFList = () => {
  const { data: session, status } = useSession();
  const [pdfs, setPdfs] = useState<PDFDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchPDFs = async () => {
      try {
        // First check if user is authenticated
        if (status === 'loading') {
          return; // Wait until session is loaded
        }

        if (status === 'unauthenticated' || !session) {
          throw new Error('Not authenticated');
        }

        setLoading(true);
        const response = await pdfService.getPDFs();

        if (response.error) {
          throw new Error(response.error);
        }

        setPdfs(response.data || []);
      } catch (err) {
        console.error('Error fetching PDFs:', err);
        if (err instanceof Error && err.message === 'Not authenticated') {
          setError('Please log in to view your PDFs.');
        } else {
          setError('Failed to load PDFs. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPDFs();
  }, [session, status]);

  if (loading) {
    return (
      <div className="p-4 flex justify-center items-center">
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return <div className="p-4 bg-red-50 text-red-500 rounded-md">{error}</div>;
  }

  if (pdfs.length === 0) {
    return (
      <div className="p-8 text-center bg-white shadow-md rounded-lg">
        <p className="text-gray-500 mb-4">No PDFs uploaded yet.</p>
        <p className="text-sm text-gray-400">Upload your first PDF to get started.</p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow-md rounded-lg">
      <h2 className="text-xl font-semibold p-6 border-b">Your PDFs</h2>
      <div className="divide-y">
        {pdfs.map((pdf) => (
          <Link
            key={pdf.id}
            href={`/pdf/${pdf.id}`}
            className="block p-6 hover:bg-gray-50 transition"
          >
            <div className="flex justify-between items-center">
              <div>
                <h3 className="font-medium text-lg">{pdf.title}</h3>
                {pdf.description && (
                  <p className="text-gray-600 mt-1 line-clamp-2">{pdf.description}</p>
                )}
                <div className="flex space-x-4 mt-2">
                  <p className="text-gray-500 text-sm">
                    <span
                      className="inline-block w-2 h-2 rounded-full mr-1 align-middle"
                      style={{
                        backgroundColor:
                          pdf.status === 'completed'
                            ? '#10B981'
                            : pdf.status === 'processing'
                              ? '#F59E0B'
                              : pdf.status === 'error'
                                ? '#EF4444'
                                : '#6B7280',
                      }}
                    ></span>
                    <span className="capitalize">{pdf.status}</span>
                  </p>
                  <p className="text-gray-500 text-sm">
                    {pdf.page_count ? `${pdf.page_count} pages` : ''}
                  </p>
                  <p className="text-gray-500 text-sm">
                    {new Date(pdf.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5 text-gray-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default PDFList;
