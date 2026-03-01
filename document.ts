export interface Document {
  id: string;
  userId: string;
  filename: string;
  s3Key: string;
  uploadedAt: string;
  fileSize: number;
  pageCount: number;
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed';
}

export interface UploadProgress {
  documentId: string;
  progress: number;
  status: string;
}

export interface UploadError {
  message: string;
  code?: string;
}
