/**
 * Utilities for authentication
 */

/**
 * Create a simple mock token for use with the backend
 * This is NOT for production use, just for development
 */
export function createToken(payload: any): string {
  try {
    // For development: create a simple mock token
    // In a real app, you would use proper JWT encoding
    const tokenData = {
      ...payload,
      exp: Math.floor(Date.now() / 1000) + 24 * 60 * 60, // 24 hours
    };

    // Base64 encode the token data
    const token = btoa(JSON.stringify(tokenData));
    return token;
  } catch (error) {
    console.error('Error creating token:', error);
    // Fallback token
    return `mock-token-${Date.now()}`;
  }
}
