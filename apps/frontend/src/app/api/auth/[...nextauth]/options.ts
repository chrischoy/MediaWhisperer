import { NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { createToken } from '@/lib/auth-utils'; // We'll create this utility

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Mock user database
const users = [
  {
    id: '1',
    name: 'Admin',
    email: 'admin@example.com',
    password: 'password',
  },
];

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        try {
          // Call FastAPI login endpoint
          const response = await fetch(`${API_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
              username: credentials.email, // FastAPI OAuth2 expects 'username'
              password: credentials.password,
            }),
          });

          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.detail || 'Authentication failed');
          }

          // FastAPI returns a token - we need to decode it to get user info
          // For simplicity, we're creating a simplified user object
          return {
            id: 'api-user', // This will be replaced by the token
            name: credentials.email,
            email: credentials.email,
            // Store the token for use in API calls
            accessToken: data.access_token,
          };
        } catch (error) {
          console.error('Auth error:', error);

          // Fallback to mock database if API call fails
          // This can be helpful during development if the API is not running
          const user = users.find(
            (user) => user.email === credentials.email && user.password === credentials.password
          );

          if (user) {
            console.log('Using mock database for authentication');

            // Create a mock token for the user
            const mockToken = createToken({ sub: user.id });

            return {
              id: user.id,
              name: user.name,
              email: user.email,
              // Add a mock access token
              accessToken: mockToken,
            };
          }

          return null;
        }
      },
    }),
  ],
  pages: {
    signIn: '/login',
  },
  session: {
    strategy: 'jwt',
  },
  callbacks: {
    async jwt({ token, user }) {
      // Initial sign in
      if (user) {
        token.id = user.id;
        token.accessToken = user.accessToken; // Store the API token
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        // Add the access token to the session
        session.accessToken = token.accessToken as string;
      }
      return session;
    },
  },
};
