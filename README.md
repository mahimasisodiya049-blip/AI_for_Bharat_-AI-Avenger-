# Document Upload Components

This directory contains the frontend components for document upload and management functionality.

## Components

### DocumentUploader

A component that handles PDF file uploads with the following features:

- **File Validation**: Validates file type (PDF only) and size (max 50MB) before upload
- **Progress Bar**: Shows real-time upload progress
- **Error Handling**: Displays user-friendly error messages
- **Drag & Drop**: Supports drag-and-drop file selection (via native file input)

**Props:**
- `onUploadSuccess?: (documentId: string) => void` - Callback when upload succeeds
- `onUploadError?: (error: string) => void` - Callback when upload fails

**Usage:**
```tsx
<DocumentUploader
  onUploadSuccess={(id) => console.log('Uploaded:', id)}
  onUploadError={(error) => console.error('Error:', error)}
/>
```

### DocumentList

A component that displays a list of uploaded documents with the following features:

- **Document Display**: Shows filename, size, page count, and upload date
- **Status Badges**: Visual indicators for processing status (pending, processing, completed, failed)
- **Delete Functionality**: Allows users to delete documents with confirmation
- **Refresh**: Manual refresh button to reload the document list
- **Empty State**: Friendly message when no documents exist
- **Loading State**: Skeleton loading animation while fetching

**Props:**
- `refreshTrigger?: number` - Change this value to trigger a refresh
- `onDocumentSelect?: (document: Document) => void` - Callback when a document is clicked

**Usage:**
```tsx
<DocumentList
  refreshTrigger={refreshCounter}
  onDocumentSelect={(doc) => console.log('Selected:', doc)}
/>
```

## Validation

The `validation.ts` utility provides:

- **File Type Validation**: Ensures only PDF files are accepted
- **File Size Validation**: Enforces 50MB maximum file size
- **Empty File Check**: Prevents uploading empty files
- **File Size Formatting**: Converts bytes to human-readable format (KB, MB, GB)

## API Integration

The `api.ts` utility provides:

- **uploadDocument**: Uploads a file with progress tracking using XMLHttpRequest
- **getDocuments**: Fetches the list of user's documents
- **deleteDocument**: Deletes a document by ID

All API calls include JWT token authentication from localStorage.

## Requirements Satisfied

This implementation satisfies the following requirements from the spec:

- **Requirement 2.1**: File type and size validation before upload
- **Requirement 2.2**: PDF upload with progress indication
- **Requirement 7.6**: Upload progress display and confirmation

## Styling

Components use Tailwind CSS for styling with:
- Responsive design
- Hover states and transitions
- Loading animations
- Color-coded status indicators
- Accessible SVG icons
