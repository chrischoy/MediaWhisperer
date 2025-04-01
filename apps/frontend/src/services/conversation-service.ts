import { apiClient } from './api-client';

export interface Message {
  id: number;
  content: string;
  role: 'user' | 'assistant' | 'system';
  created_at: string;
}

export interface Conversation {
  id: number;
  title: string;
  pdf_id: number;
  created_at: string;
  updated_at?: string;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

export interface ConversationListItem extends Conversation {
  message_count: number;
}

export interface ConversationCreate {
  pdf_id: number;
  title?: string;
}

export interface MessageCreate {
  content: string;
}

export class ConversationService {
  /**
   * Get all conversations, optionally filtered by PDF ID
   */
  async getConversations(pdfId?: string | number) {
    const options = pdfId ? { params: { pdf_id: pdfId } } : undefined;
    return apiClient.get<ConversationListItem[]>('/conversations', options);
  }

  /**
   * Get a specific conversation with its messages
   */
  async getConversation(id: string | number) {
    return apiClient.get<ConversationWithMessages>(`/conversations/${id}`);
  }

  /**
   * Create a new conversation for a PDF
   */
  async createConversation(data: ConversationCreate) {
    return apiClient.post<Conversation>('/conversations', data);
  }

  /**
   * Add a new message to a conversation
   */
  async addMessage(conversationId: string | number, content: string) {
    return apiClient.post<Message>(`/conversations/${conversationId}/messages`, {
      content,
    });
  }

  /**
   * Delete a conversation
   */
  async deleteConversation(id: string | number) {
    return apiClient.delete<void>(`/conversations/${id}`);
  }
}

// Create singleton instance
export const conversationService = new ConversationService();
