'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import rehypeKatex from 'rehype-katex';
import remarkMath from 'remark-math';
import rehypeHighlight from 'rehype-highlight';
import 'katex/dist/katex.min.css';
import { pdfService, conversationService, PDFDocument, ConversationListItem } from '@/services';

// Custom Markdown styles component
const MarkdownContent = ({ content }: { content: string }) => {
  // Process content to hide span tags with page IDs
  const processedContent = content?.replace(/<span\s+id="page-\d+-\d+"><\/span>/g, '');

  return (
    <div className="markdown-body">
      <style jsx global>{`
        .markdown-body h1 {
          font-size: 2.5rem;
          font-weight: 700;
          margin-top: 2rem;
          margin-bottom: 1.5rem;
          color: #1a202c;
          border-bottom: 1px solid #eaeaea;
          padding-bottom: 0.5rem;
        }

        .markdown-body h2 {
          font-size: 2rem;
          font-weight: 600;
          margin-top: 2rem;
          margin-bottom: 1rem;
          color: #2d3748;
        }

        .markdown-body h3 {
          font-size: 1.5rem;
          font-weight: 600;
          margin-top: 1.5rem;
          margin-bottom: 0.75rem;
          color: #4a5568;
        }

        .markdown-body p {
          margin-bottom: 1.25rem;
          line-height: 1.7;
          color: #4a5568;
        }

        .markdown-body a {
          color: #3182ce;
          text-decoration: none;
        }

        .markdown-body a:hover {
          text-decoration: underline;
        }

        .markdown-body code {
          background-color: #f7fafc;
          padding: 0.2em 0.4em;
          border-radius: 0.25rem;
          font-family: Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
          font-size: 0.9em;
          color: #2d3748;
        }

        .markdown-body pre {
          background-color: #f7fafc;
          padding: 1rem;
          border-radius: 0.5rem;
          overflow-x: auto;
          margin: 1.5rem 0;
        }

        .markdown-body pre code {
          background-color: transparent;
          padding: 0;
          border-radius: 0;
        }

        .markdown-body blockquote {
          border-left: 4px solid #3182ce;
          padding-left: 1rem;
          font-style: italic;
          color: #4a5568;
          background-color: #ebf8ff;
          padding: 0.5rem 1rem;
          border-radius: 0 0.5rem 0.5rem 0;
          margin: 1.5rem 0;
        }

        .markdown-body ul,
        .markdown-body ol {
          padding-left: 2rem;
          margin: 1rem 0;
        }

        .markdown-body ul {
          list-style-type: disc;
        }

        .markdown-body ol {
          list-style-type: decimal;
        }

        .markdown-body li {
          margin: 0.5rem 0;
        }

        .markdown-body img {
          max-width: 100%;
          border-radius: 0.5rem;
          margin: 2rem 0;
          box-shadow:
            0 4px 6px -1px rgba(0, 0, 0, 0.1),
            0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        .markdown-body hr {
          border: 0;
          border-top: 1px solid #e2e8f0;
          margin: 2rem 0;
        }

        /* Enhanced table styles */
        .markdown-body table {
          width: 100%;
          border-collapse: separate;
          border-spacing: 0;
          margin: 1.5rem 0;
          border-radius: 0.5rem;
          overflow: hidden;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .markdown-body th {
          background-color: #4299e1;
          color: white;
          font-weight: 600;
          text-align: left;
          padding: 0.75rem 1rem;
          border: none;
        }

        .markdown-body td {
          padding: 0.75rem 1rem;
          border-bottom: 1px solid #e2e8f0;
          border-right: 1px solid #e2e8f0;
        }

        .markdown-body td:last-child {
          border-right: none;
        }

        .markdown-body tr:last-child td {
          border-bottom: none;
        }

        .markdown-body tr:nth-child(even) {
          background-color: #f7fafc;
        }

        .markdown-body tr:hover {
          background-color: #ebf8ff;
        }

        /* KaTeX math styles */
        .markdown-body .katex-display {
          margin: 1.5rem 0;
          overflow-x: auto;
          overflow-y: hidden;
        }

        .markdown-body .katex {
          font-size: 1.1em;
        }
      `}</style>
      <ReactMarkdown
        rehypePlugins={[rehypeRaw, rehypeKatex, rehypeHighlight]}
        remarkPlugins={[remarkMath]}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
};

const PDFDetailPage = () => {
  const params = useParams();
  const router = useRouter();
  const [pdf, setPdf] = useState<PDFDocument | null>(null);
  const [conversations, setConversations] = useState<ConversationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [creatingConversation, setCreatingConversation] = useState(false);
  const [activeTab, setActiveTab] = useState<'details' | 'content'>('details');
  const [conversationError, setConversationError] = useState<string | null>(null);

  const pdfId = Array.isArray(params.id) ? params.id[0] : params.id;

  // Fetch PDF data
  useEffect(() => {
    const fetchPDF = async () => {
      try {
        setLoading(true);
        console.log(`Fetching PDF with ID: ${pdfId}`);
        const response = await pdfService.getPDF(pdfId);

        if (response.error) {
          console.error(`Error response:`, response);
          throw new Error(response.error);
        }

        if (!response.data) {
          throw new Error('No PDF data returned');
        }

        console.log(`PDF data loaded:`, response.data);
        setPdf(response.data);

        // Fetch conversations for this PDF
        try {
          const conversationsResponse = await conversationService.getConversations(pdfId);
          if (conversationsResponse.data) {
            setConversations(conversationsResponse.data);
          }
        } catch (convError) {
          console.error('Error fetching conversations:', convError);
          setConversationError(
            'Unable to load conversations. This feature may be temporarily unavailable.'
          );
          // Don't throw the error, just set the error state
        }
      } catch (err) {
        console.error('Error fetching PDF:', err);
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(`Failed to load PDF: ${message}. Please try again.`);
      } finally {
        setLoading(false);
      }
    };

    if (pdfId) {
      fetchPDF();
    }
  }, [pdfId]);

  // Create a new conversation
  const startNewConversation = async () => {
    try {
      setCreatingConversation(true);
      setConversationError(null);

      const response = await conversationService.createConversation({
        pdf_id: Number(pdfId),
        title: `Chat about ${pdf?.title || 'PDF'}`,
      });

      if (response.error) {
        throw new Error(response.error);
      }

      if (response.data) {
        // Navigate to the conversation
        router.push(`/pdf/${pdfId}/conversation/${response.data.id}`);
      }
    } catch (err) {
      console.error('Error creating conversation:', err);
      setConversationError(
        'Failed to start conversation. This feature may be temporarily unavailable.'
      );
      setCreatingConversation(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <p className="text-red-500 mb-4">{error}</p>
        <Link href="/dashboard" className="text-blue-500 hover:underline">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  if (!pdf) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <p className="text-gray-500 mb-4">PDF not found or you don't have access.</p>
        <Link href="/dashboard" className="text-blue-500 hover:underline">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
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

      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <h1 className="text-2xl font-bold mb-2">{pdf.title}</h1>
        {pdf.description && <p className="text-gray-600 mb-4">{pdf.description}</p>}

        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-4">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('details')}
              className={`${
                activeTab === 'details'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Details
            </button>
            <button
              onClick={() => setActiveTab('content')}
              className={`${
                activeTab === 'content'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Content
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'details' ? (
          <>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-gray-500 text-sm">Filename</p>
                <p>{pdf.filename}</p>
              </div>
              <div>
                <p className="text-gray-500 text-sm">Status</p>
                <p className="capitalize">{pdf.status}</p>
              </div>
              <div>
                <p className="text-gray-500 text-sm">Pages</p>
                <p>{pdf.page_count || 'Unknown'}</p>
              </div>
              <div>
                <p className="text-gray-500 text-sm">Uploaded</p>
                <p>{new Date(pdf.created_at).toLocaleDateString()}</p>
              </div>
            </div>

            {conversationError ? (
              <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded mb-4">
                {conversationError}
              </div>
            ) : (
              <>
                <button
                  onClick={startNewConversation}
                  disabled={creatingConversation || pdf.status !== 'completed'}
                  className="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 disabled:opacity-50 transition"
                >
                  {creatingConversation ? 'Starting Conversation...' : 'Start New Conversation'}
                </button>

                {pdf.status !== 'completed' && (
                  <p className="text-yellow-600 text-sm mt-2">
                    PDF processing must be completed before starting a conversation.
                  </p>
                )}
              </>
            )}
          </>
        ) : (
          <div className="max-w-none">
            {pdf.markdown ? (
              <MarkdownContent content={pdf.markdown} />
            ) : (
              <p className="text-gray-500">
                No content available yet. The PDF is still being processed.
              </p>
            )}
            {pdf.images && pdf.images.length > 0 && (
              <div className="mt-8">
                <h2 className="text-xl font-semibold mb-4">Images</h2>
                <div className="grid grid-cols-2 gap-4">
                  {pdf.images.map((image, index) => (
                    <img
                      key={index}
                      src={image}
                      alt={`PDF image ${index + 1}`}
                      className="rounded-lg shadow-md"
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {conversations.length > 0 && !conversationError && (
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Conversations</h2>
          <div className="divide-y">
            {conversations.map((conversation) => (
              <Link
                key={conversation.id}
                href={`/pdf/${pdfId}/conversation/${conversation.id}`}
                className="block py-4 hover:bg-gray-50 transition"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-medium">{conversation.title}</h3>
                    <p className="text-gray-500 text-sm">
                      {conversation.message_count} message
                      {conversation.message_count !== 1 ? 's' : ''} •
                      {new Date(conversation.created_at).toLocaleDateString()}
                    </p>
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
      )}
    </div>
  );
};

export default PDFDetailPage;
