/**
 * Base API client with common functionality for making requests to the backend
 */

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

export interface ApiRequestOptions {
  headers?: Record<string, string>;
  params?: Record<string, string | number | boolean>;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl || '';
  }

  /**
   * Format URL with query parameters
   */
  private formatUrl(path: string, options?: ApiRequestOptions): string {
    const url = `${this.baseUrl}${path}`;
    
    if (!options?.params) {
      return url;
    }
    
    const queryParams = new URLSearchParams();
    Object.entries(options.params).forEach(([key, value]) => {
      queryParams.append(key, String(value));
    });
    
    return `${url}?${queryParams.toString()}`;
  }

  /**
   * Make a generic request to the API
   */
  private async request<T>(
    method: string,
    path: string,
    body?: any,
    options?: ApiRequestOptions
  ): Promise<ApiResponse<T>> {
    try {
      const url = this.formatUrl(path, options);
      
      const headers = {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      };
      
      const config: RequestInit = {
        method,
        headers,
        credentials: 'include',
      };
      
      if (body && method !== 'GET') {
        config.body = JSON.stringify(body);
      }
      
      const response = await fetch(url, config);
      const status = response.status;
      
      // For 204 No Content responses
      if (status === 204) {
        return { status, data: undefined };
      }
      
      let data;
      try {
        data = await response.json();
      } catch (e) {
        data = undefined;
      }
      
      if (!response.ok) {
        return {
          status,
          error: data?.message || data?.detail || `Request failed with status ${status}`,
        };
      }
      
      return { status, data };
    } catch (error) {
      console.error(`API error (${method} ${path}):`, error);
      return {
        status: 0,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }

  /**
   * GET request
   */
  async get<T>(path: string, options?: ApiRequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>('GET', path, undefined, options);
  }

  /**
   * POST request
   */
  async post<T>(path: string, body?: any, options?: ApiRequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>('POST', path, body, options);
  }

  /**
   * PUT request
   */
  async put<T>(path: string, body?: any, options?: ApiRequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>('PUT', path, body, options);
  }

  /**
   * DELETE request
   */
  async delete<T>(path: string, options?: ApiRequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>('DELETE', path, undefined, options);
  }
}

// Create default API client instance
export const apiClient = new ApiClient();