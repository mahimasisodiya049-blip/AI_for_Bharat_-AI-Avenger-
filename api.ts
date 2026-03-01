/**
 * Fixed API client with proper authentication handling
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Get authentication token from localStorage
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('kirofeed_token');
}

/**
 * Upload document with progress tracking
 */
export async function uploadDocument(
  file: File,
  onProgress?: (progress: number) => void
): Promise<{ document_id: string; status: string; message: string; s3_uri: string }> {
  const formData = new FormData();
  formData.append('file', file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // Progress tracking
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && onProgress) {
        const progress = (e.loaded / e.total) * 100;
        onProgress(progress);
      }
    });

    // Success/Error handling
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          console.log('Upload success:', response);
          resolve(response);
        } catch (error) {
          console.error('Parse error:', error);
          reject(new ApiError(xhr.status, 'Invalid response format'));
        }
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          console.error('Upload error:', error);
          reject(new ApiError(xhr.status, error.detail || error.message || 'Upload failed'));
        } catch {
          reject(new ApiError(xhr.status, `Upload failed with status ${xhr.status}`));
        }
      }
    });

    xhr.addEventListener('error', () => {
      console.error('Network error during upload');
      reject(new ApiError(0, 'Network error occurred'));
    });

    xhr.addEventListener('abort', () => {
      console.log('Upload cancelled');
      reject(new ApiError(0, 'Upload cancelled'));
    });

    // Open connection
    xhr.open('POST', `${API_BASE_URL}/documents/upload`);
    
    // Add auth token
    const token = getAuthToken();
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      console.log('Auth token added to upload request');
    } else {
      console.warn('No auth token found for upload');
    }

    // Send request
    xhr.send(formData);
  });
}

/**
 * Get list of documents
 */
export async function getDocuments(): Promise<any[]> {
  try {
    const token = getAuthToken();
    
    if (!token) {
      console.warn('No auth token found - user may not be logged in');
      throw new ApiError(401, 'Not authenticated. Please log in.');
    }
    
    console.log('Fetching documents with token');
    
    const response = await fetch(`${API_BASE_URL}/documents`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch documents' }));
      console.error('Fetch documents error:', errorData);
      throw new ApiError(response.status, errorData.detail || 'Failed to fetch documents');
    }

    const data = await response.json();
    console.log('Documents fetched:', data);
    return data.documents || [];
  } catch (error) {
    console.error('Error in getDocuments:', error);
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, 'Network error occurred');
  }
}

/**
 * Delete a document
 */
export async function deleteDocument(documentId: string): Promise<void> {
  try {
    const token = getAuthToken();
    
    if (!token) {
      throw new ApiError(401, 'Not authenticated. Please log in.');
    }
    
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to delete document' }));
      throw new ApiError(response.status, errorData.detail || 'Failed to delete document');
    }
  } catch (error) {
    console.error('Error in deleteDocument:', error);
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, 'Network error occurred');
  }
}
