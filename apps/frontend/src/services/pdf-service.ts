import { apiClient } from './api-client';

export interface PDFDocument {
  id: number;
  title: string;
  description?: string;
  filename: string;
  status: string;
  page_count?: number;
  created_at: string;
}

export interface PDFUploadResponse {
  id: number;
  title: string;
  status: string;
}

export class PDFService {
  /**
   * Get a list of all PDFs for the current user
   */
  async getPDFs() {
    return apiClient.get<PDFDocument[]>('/api/pdf/list');
  }

  /**
   * Get details for a specific PDF
   */
  async getPDF(id: string | number) {
    return apiClient.get<PDFDocument>(`/api/pdf/${id}`);
  }

  /**
   * Get the processed content of a PDF
   */
  async getPDFContent(id: string | number) {
    return apiClient.get<{ content: string }>(`/api/pdf/${id}/content`);
  }

  /**
   * Get the summary of a PDF
   */
  async getPDFSummary(id: string | number) {
    return apiClient.get<{ summary: string }>(`/api/pdf/${id}/summary`);
  }

  /**
   * Upload a new PDF
   */
  async uploadPDF(formData: FormData) {
    // Use native fetch for multipart/form-data
    try {
      const response = await fetch('/api/pdf/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });
      
      const status = response.status;
      
      if (!response.ok) {
        let errorMessage = 'Failed to upload PDF';
        try {
          const errorData = await response.json();
          errorMessage = errorData.message || errorData.detail || errorMessage;
        } catch (e) {
          // Use default error message
        }
        
        return { status, error: errorMessage };
      }
      
      const data = await response.json();
      return { status, data };
    } catch (error) {
      console.error('Error uploading PDF:', error);
      return {
        status: 0,
        error: error instanceof Error ? error.message : 'Unknown error occurred during upload',
      };
    }
  }
}

// Create singleton instance
export const pdfService = new PDFService();