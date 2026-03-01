import { validateFile, formatFileSize } from '../validation';

describe('validateFile', () => {
  it('should accept valid PDF files under 50MB', () => {
    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });
    Object.defineProperty(file, 'size', { value: 1024 * 1024 }); // 1MB

    const result = validateFile(file);
    expect(result.valid).toBe(true);
    expect(result.error).toBeUndefined();
  });

  it('should reject non-PDF files', () => {
    const file = new File(['test content'], 'test.txt', {
      type: 'text/plain',
    });

    const result = validateFile(file);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Only PDF files are allowed');
  });

  it('should reject files over 50MB', () => {
    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });
    Object.defineProperty(file, 'size', { value: 51 * 1024 * 1024 }); // 51MB

    const result = validateFile(file);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('File size must not exceed 50MB');
  });

  it('should reject empty files', () => {
    const file = new File([], 'test.pdf', {
      type: 'application/pdf',
    });

    const result = validateFile(file);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('File is empty');
  });
});

describe('formatFileSize', () => {
  it('should format bytes correctly', () => {
    expect(formatFileSize(0)).toBe('0 Bytes');
    expect(formatFileSize(1024)).toBe('1 KB');
    expect(formatFileSize(1024 * 1024)).toBe('1 MB');
    expect(formatFileSize(1536 * 1024)).toBe('1.5 MB');
  });
});
