'use client';

import { useState } from 'react';
import { pdfService } from '@/services';
import { useRouter } from 'next/navigation';

interface PDFUploadFromUrlProps {
  onUploadSuccess?: () => void;
}

const PDFUploadFromUrl: React.FC<PDFUploadFromUrlProps> = ({ onUploadSuccess }) => {
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!url.trim()) {
      setError('Please enter a PDF URL');
      return;
    }

    try {
      setUploading(true);
      setError('');

      const response = await pdfService.uploadFromUrl({
        url,
        title: title.trim() ? title : undefined,
        description: description.trim() ? description : undefined,
      });

      if (response.error) {
        throw new Error(response.error);
      }

      if (response.data) {
        // Reset form
        setUrl('');
        setTitle('');
        setDescription('');

        // Callback or redirect
        if (onUploadSuccess) {
          onUploadSuccess();
        } else {
          router.push(`/pdf/${response.data.id}`);
        }
      }
    } catch (err) {
      console.error('Error uploading PDF from URL:', err);
      setError(
        'Failed to upload PDF from URL. Please ensure the URL is correct and points to a valid PDF file.'
      );
    } finally {
      setUploading(false);
    }
  };

  const handleArxivPaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    const pastedText = e.clipboardData.getData('text');

    // Check for arXiv identifier patterns
    // Examples:
    // - https://arxiv.org/abs/2304.09871
    // - arXiv:2304.09871
    const arxivAbsRegex = /arxiv\.org\/abs\/(\d+\.\d+)/i;
    const arxivIdRegex = /arxiv:(\d+\.\d+)/i;

    let arxivId: string | null = null;

    // Extract arXiv ID
    const absMatch = pastedText.match(arxivAbsRegex);
    const idMatch = pastedText.match(arxivIdRegex);

    if (absMatch && absMatch[1]) {
      arxivId = absMatch[1];
    } else if (idMatch && idMatch[1]) {
      arxivId = idMatch[1];
    }

    // Convert to PDF URL if possible
    if (arxivId) {
      const pdfUrl = `https://arxiv.org/pdf/${arxivId}.pdf`;
      e.preventDefault();
      setUrl(pdfUrl);
    }
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Upload PDF from URL</h2>

      <form onSubmit={handleSubmit}>
        {error && <div className="mb-4 p-3 text-sm bg-red-50 text-red-500 rounded-md">{error}</div>}

        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="pdf-url">
            PDF URL
          </label>
          <div className="mb-1">
            <input
              type="url"
              id="pdf-url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onPaste={handleArxivPaste}
              className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="https://example.com/document.pdf"
              disabled={uploading}
              required
            />
          </div>
          <p className="text-xs text-gray-500">
            Tip: For arXiv papers, you can paste the arXiv URL or ID and it will be converted
            automatically.
          </p>
        </div>

        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="pdf-title">
            Title (Optional)
          </label>
          <input
            type="text"
            id="pdf-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter a title for this PDF"
            disabled={uploading}
          />
        </div>

        <div className="mb-6">
          <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="pdf-description">
            Description (Optional)
          </label>
          <textarea
            id="pdf-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter a description for this PDF"
            rows={3}
            disabled={uploading}
          />
        </div>

        <button
          type="submit"
          className="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 disabled:opacity-50 transition"
          disabled={uploading || !url.trim()}
        >
          {uploading ? (
            <div className="flex justify-center items-center">
              <div className="h-5 w-5 border-t-2 border-b-2 border-white rounded-full animate-spin mr-2"></div>
              Processing...
            </div>
          ) : (
            'Process PDF'
          )}
        </button>
      </form>
    </div>
  );
};

export default PDFUploadFromUrl;
