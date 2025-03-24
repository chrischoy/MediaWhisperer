'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { conversationService, ConversationWithMessages, Message } from '@/services';

const ConversationPage = () => {
  const params = useParams();
  const router = useRouter();
  const [conversation, setConversation] = useState<ConversationWithMessages | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const pdfId = params.id;
  const conversationId = params.conversationId;

  // Fetch conversation data
  useEffect(() => {
    const fetchConversation = async () => {
      try {
        setLoading(true);
        const response = await conversationService.getConversation(conversationId);
        
        if (response.error) {
          throw new Error(response.error);
        }
        
        setConversation(response.data || null);
      } catch (err) {
        console.error('Error fetching conversation:', err);
        setError('Failed to load conversation. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    if (conversationId) {
      fetchConversation();
    }
  }, [conversationId]);

  // Scroll to bottom of messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversation?.messages]);

  // Send a new message
  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!message.trim() || sending) return;
    
    try {
      setSending(true);
      
      const response = await conversationService.addMessage(conversationId, message);
      
      if (response.error) {
        throw new Error(response.error);
      }
      
      // Refetch the conversation to get the updated messages including AI response
      const updatedConversation = await conversationService.getConversation(conversationId);
      if (updatedConversation.data) {
        setConversation(updatedConversation.data);
      }
      setMessage('');
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to send message. Please try again.');
    } finally {
      setSending(false);
    }
  };

  // Handle back button
  const handleBack = () => {
    router.push(`/pdf/${pdfId}`);
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
        <button 
          onClick={handleBack}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Back to PDF
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen max-h-screen">
      {/* Header */}
      <div className="bg-white shadow p-4 flex items-center">
        <button 
          onClick={handleBack}
          className="mr-4 text-gray-600 hover:text-gray-900"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <h1 className="text-xl font-semibold truncate">
          {conversation?.title || 'Conversation'}
        </h1>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
        <div className="max-w-3xl mx-auto space-y-4">
          {conversation?.messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div 
                className={`max-w-[80%] p-3 rounded-lg ${
                  msg.role === 'user' 
                    ? 'bg-blue-500 text-white' 
                    : msg.role === 'system' 
                      ? 'bg-gray-300 text-gray-700'
                      : 'bg-white border border-gray-200 text-gray-700'
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
                <div 
                  className={`text-xs mt-1 ${
                    msg.role === 'user' ? 'text-blue-100' : 'text-gray-400'
                  }`}
                >
                  {new Date(msg.created_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>
      
      {/* Message Input */}
      <div className="bg-white border-t p-4">
        <form onSubmit={sendMessage} className="max-w-3xl mx-auto flex">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask a question about this PDF..."
            className="flex-1 border border-gray-300 rounded-l-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={sending}
          />
          <button
            type="submit"
            className="bg-blue-500 text-white px-4 py-2 rounded-r-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            disabled={sending || !message.trim()}
          >
            {sending ? (
              <div className="h-5 w-5 border-t-2 border-b-2 border-white rounded-full animate-spin"></div>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ConversationPage;