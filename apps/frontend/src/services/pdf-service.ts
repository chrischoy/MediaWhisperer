import { apiClient } from './api-client';

export interface PDFDocument {
  id: number;
  title: string;
  description?: string;
  filename: string;
  status: string;
  page_count?: number;
  created_at: string;
  markdown?: string;
  images?: string[];
}

export interface PDFUploadResponse {
  id: number;
  title: string;
  status: string;
}

export interface PDFFromURL {
  url: string;
  title?: string;
  description?: string;
}

export class PDFService {
  /**
   * Get a list of all PDFs for the current user
   */
  async getPDFs() {
    return apiClient.get<PDFDocument[]>('/pdf/list');
  }

  /**
   * Get details for a specific PDF
   */
  async getPDF(id: string | number) {
    console.log(`Fetching PDF with ID: ${id}`);
    // Ensure id is treated as a number for compatibility with backend
    const numericId = typeof id === 'string' ? parseInt(id, 10) : id;
    if (isNaN(numericId)) {
      console.error(`Invalid PDF ID: ${id}`);
      return {
        status: 400,
        error: 'Invalid PDF ID',
      };
    }

    try {
      const response = await apiClient.get<PDFDocument>(`/pdf/${numericId}`);
      console.log(`PDF fetch response:`, response);

      // If we have data, ensure it's properly structured
      if (response.data) {
        // Log the full response data for debugging
        console.log('Full PDF data:', response.data);

        // If markdown is not in the main response, try to fetch it separately
        if (!response.data.markdown) {
          try {
            const contentResponse = await this.getPDFContent(numericId);
            if (contentResponse.data) {
              response.data.markdown = contentResponse.data.markdown;
              response.data.images = contentResponse.data.images;
              console.log('Updated PDF data with content:', response.data);
            }
          } catch (contentError) {
            console.error('Error fetching PDF content:', contentError);
          }
        }
      }

      return response;
    } catch (error) {
      console.error(`Error fetching PDF ${numericId}:`, error);
      return {
        status: 500,
        error: error instanceof Error ? error.message : 'Unknown error fetching PDF',
      };
    }
  }

  /**
   * Get the processed content of a PDF
   */
  async getPDFContent(id: string | number) {
    return apiClient.get<{ markdown: string; images: string[] }>(`/pdf/${id}/content`);
  }

  /**
   * Get the summary of a PDF
   */
  async getPDFSummary(id: string | number) {
    return apiClient.get<{ summary: string }>(`/pdf/${id}/summary`);
  }

  /**
   * Format URL for special cases like arXiv
   */
  private formatPDFUrl(url: string): string {
    // Handle arXiv URLs
    if (url.includes('arxiv.org/pdf/') && !url.endsWith('.pdf')) {
      return `${url}.pdf`;
    }
    return url;
  }

  /**
   * Upload a PDF from a URL
   */
  async uploadFromUrl(data: PDFFromURL) {
    // Format the URL for special cases
    const formattedUrl = this.formatPDFUrl(data.url);

    return apiClient.post<PDFUploadResponse>('/pdf/from-url', {
      ...data,
      url: formattedUrl,
    });
  }

  /**
   * Upload a new PDF
   */
  async uploadPDF(formData: FormData) {
    // Use native fetch for multipart/form-data
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const API_PREFIX = '/api'; // Added API prefix to match FastAPI's settings

      const response = await fetch(`${API_URL}${API_PREFIX}/pdf/upload`, {
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
