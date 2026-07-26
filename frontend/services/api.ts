import apiClient from '@/lib/axios-client';
import { ApiResponse, User } from '@/types';

/**
 * API Service Layer
 * Centralized API requests
 */

class ApiService {
  // Example: User endpoints
  async getUser(userId: string): Promise<User> {
    const response = await apiClient.get<ApiResponse<User>>(`/api/v1/users/${userId}`);
    return response.data.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<ApiResponse<User>>('/api/v1/users/me');
    return response.data.data;
  }

  // Add more API methods here as needed
}

export const apiService = new ApiService();
