"""
Document management routes with comprehensive error handling.
"""

from fastapi import APIRouter, Depends, UploadFile, File
from auth import verify_token, TokenPayload
from services.document_service import (
    upload_document_to_s3,
    get_user_documents,
    DocumentUploadResponse,
    DocumentListResponse
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: TokenPayload = Depends(verify_token)
):
    """
    Upload a PDF document to S3.
    
    - Validates file type (PDF only)
    - Validates file size (max 50MB)
    - Stores in S3 with encryption
    - Records metadata in DynamoDB
    - Returns S3 URI and document metadata
    """
    return await upload_document_to_s3(file, current_user.sub)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    current_user: TokenPayload = Depends(verify_token)
):
    """
    Retrieve all documents for the authenticated user.
    
    Returns a list of document metadata from DynamoDB.
    """
    return get_user_documents(current_user.sub)
