'use client';

import { useState } from 'react';
import { pdfService } from '@/services';
import { useRouter } from 'next/navigation';

interface PDFUploadProps {
  onUploadSuccess?: () => void;
}

const PDFUpload: React.FC<PDFUploadProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      if (!title) {
        // Use the filename (without extension) as the default title
        const fileName = selectedFile.name.split('.').slice(0, -1).join('.');
        setTitle(fileName);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a PDF file to upload');
      return;
    }
    
    if (!title.trim()) {
      setError('Please enter a title for the PDF');
      return;
    }
    
    try {
      setUploading(true);
      setError('');
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);
      
      if (description.trim()) {
        formData.append('description', description);
      }
      
      const response = await pdfService.uploadPDF(formData);
      
      if (response.error) {
        throw new Error(response.error);
      }
      
      if (response.data) {
        // Reset form
        setFile(null);
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
      console.error('Error uploading PDF:', err);
      setError('Failed to upload PDF. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Upload PDF</h2>
      
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="mb-4 p-3 text-sm bg-red-50 text-red-500 rounded-md">
            {error}
          </div>
        )}
        
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="pdf-file">
            PDF File
          </label>
          <input
            type="file"
            id="pdf-file"
            accept=".pdf"
            onChange={handleFileChange}
            className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={uploading}
            required
          />
          {file && (
            <p className="mt-1 text-sm text-gray-500">
              Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
            </p>
          )}
        </div>
        
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="pdf-title">
            Title
          </label>
          <input
            type="text"
            id="pdf-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter a title for this PDF"
            disabled={uploading}
            required
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
          disabled={uploading || !file}
        >
          {uploading ? (
            <div className="flex justify-center items-center">
              <div className="h-5 w-5 border-t-2 border-b-2 border-white rounded-full animate-spin mr-2"></div>
              Uploading...
            </div>
          ) : (
            'Upload PDF'
          )}
        </button>
      </form>
    </div>
  );
};

export default PDFUpload;