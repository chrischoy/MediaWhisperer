'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { pdfService, conversationService, PDFDocument, ConversationListItem } from '@/services';

const PDFDetailPage = () => {
  const params = useParams();
  const router = useRouter();
  const [pdf, setPdf] = useState<PDFDocument | null>(null);
  const [conversations, setConversations] = useState<ConversationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [creatingConversation, setCreatingConversation] = useState(false);

  const pdfId = params.id;

  // Fetch PDF data
  useEffect(() => {
    const fetchPDF = async () => {
      try {
        setLoading(true);
        const response = await pdfService.getPDF(pdfId);
        
        if (response.error) {
          throw new Error(response.error);
        }
        
        setPdf(response.data || null);
        
        // Fetch conversations for this PDF
        const conversationsResponse = await conversationService.getConversations(pdfId);
        
        if (conversationsResponse.data) {
          setConversations(conversationsResponse.data);
        }
      } catch (err) {
        console.error('Error fetching PDF:', err);
        setError('Failed to load PDF. Please try again.');
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
      
      const response = await conversationService.createConversation({
        pdf_id: Number(pdfId),
        title: `Chat about ${pdf?.title || 'PDF'}`
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
      setError('Failed to start conversation. Please try again.');
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
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z" clipRule="evenodd" />
          </svg>
          Back to Dashboard
        </Link>
      </div>
      
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <h1 className="text-2xl font-bold mb-2">{pdf.title}</h1>
        {pdf.description && (
          <p className="text-gray-600 mb-4">{pdf.description}</p>
        )}
        
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
      </div>
      
      {conversations.length > 0 && (
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
                      {conversation.message_count} message{conversation.message_count !== 1 ? 's' : ''} • 
                      {new Date(conversation.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
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