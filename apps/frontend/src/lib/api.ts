import { getSession } from 'next-auth/react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api'; // Added API prefix to match FastAPI's settings

/**
 * Make an authenticated API request to the backend
 */
export async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const session = await getSession();
  const token = session?.accessToken;

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add authorization header if we have a token
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Make sure endpoint starts with a slash if not already
  const formattedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

  // Include API prefix in all requests
  const url = `${API_URL}${API_PREFIX}${formattedEndpoint}`;

  console.log('Fetching from URL:', url);

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include', // Important for cookies
  });

  // Handle API errors
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    console.error('API Error:', error, 'Status:', response.status);
    throw new Error(error.detail || 'An error occurred while fetching data');
  }

  return response.json();
}
