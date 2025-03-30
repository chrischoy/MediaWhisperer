'use client';

import { useState, useRef } from 'react';
import { useSession } from 'next-auth/react';
import { useToast } from '@/components/ui/use-toast';

interface PDFImportProps {
  onSuccess: () => void;
}

export default function PDFImport({ onSuccess }: PDFImportProps) {
  const { data: session } = useSession();
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [input, setInput] = useState('');
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const isURL = (str: string) => {
    try {
      new URL(str);
      return true;
    } catch {
      return false;
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setInput(e.target.files[0].name);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
    // If it's a URL, clear any selected file
    if (isURL(e.target.value)) {
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFile(e.dataTransfer.files[0]);
      setInput(e.dataTransfer.files[0].name);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input && !selectedFile) {
      setError('Please enter a URL or select a file');
      return;
    }

    if (!session?.user) {
      setError('You must be logged in to upload a PDF');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Process as URL
      if (isURL(input) && !selectedFile) {
        await processURL(input);
      }
      // Process as file upload
      else if (selectedFile) {
        await uploadFile(selectedFile);
      } else {
        throw new Error('Invalid input. Please enter a valid URL or select a file.');
      }

      // Reset form
      setInput('');
      setDescription('');
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      // Trigger refresh of PDF list
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      toast({
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to process PDF',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const processURL = async (url: string) => {
    const response = await fetch('/api/pdf/from-url', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url,
        description,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to process PDF from URL');
    }

    toast({
      title: 'Success!',
      description: 'PDF from URL has been added successfully',
    });
  };

  const uploadFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      throw new Error('Only PDF files are allowed');
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('description', description);

    const response = await fetch('/api/pdf/upload', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to upload PDF');
    }

    toast({
      title: 'Success!',
      description: 'PDF uploaded successfully',
    });
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div
          className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          <div className="space-y-2">
            <div className="text-gray-600">
              <p>Drag and drop a PDF file here, or</p>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="text-blue-600 hover:text-blue-800 font-medium"
              >
                browse for a file
              </button>
              <p className="mt-1">or paste a URL to a PDF</p>
            </div>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf"
              className="hidden"
            />

            <input
              type="text"
              value={input}
              onChange={handleInputChange}
              placeholder="https://example.com/document.pdf or drag & drop"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            />
          </div>
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
            Description (optional)
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Optional description"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading}
            rows={3}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || (!input && !selectedFile)}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {isLoading
            ? 'Processing...'
            : selectedFile
              ? 'Upload PDF'
              : isURL(input)
                ? 'Add PDF from URL'
                : 'Add PDF'}
        </button>
      </form>
    </div>
  );
}
