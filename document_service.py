"""
Document service with robust error handling for AWS integrations.
"""

import boto3
import uuid
from datetime import datetime
from typing import List
from fastapi import HTTPException, UploadFile
from pydantic import BaseModel
from botocore.exceptions import NoCredentialsError, ClientError

from config import config


class DocumentMetadata(BaseModel):
    document_id: str
    user_id: str
    filename: str
    s3_key: str
    uploaded_at: str
    file_size: int
    processing_status: str = "pending"


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    file_size: int
    status: str
    message: str
    s3_uri: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentMetadata]
    total: int


def get_s3_client():
    """Get S3 client with error handling."""
    try:
        return boto3.client(
            's3',
            region_name=config.AWS_REGION,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
        )
    except NoCredentialsError:
        raise HTTPException(
            status_code=500,
            detail="AWS credentials not found. Please check your environment variables."
        )


def get_dynamodb_resource():
    """Get DynamoDB resource with error handling."""
    try:
        return boto3.resource(
            'dynamodb',
            region_name=config.AWS_REGION,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
        )
    except NoCredentialsError:
        raise HTTPException(
            status_code=500,
            detail="AWS credentials not found. Please check your environment variables."
        )


def validate_pdf_file(file: UploadFile) -> None:
    """Validate that uploaded file is a PDF."""
    # Check file extension
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are allowed."
        )
    
    # Check content type
    if file.content_type and file.content_type != 'application/pdf':
        raise HTTPException(
            status_code=400,
            detail="Invalid content type. Only PDF files (application/pdf) are allowed."
        )


async def upload_document_to_s3(
    file: UploadFile,
    user_id: str
) -> DocumentUploadResponse:
    """
    Upload document to S3 with comprehensive error handling.
    """
    try:
        # Validate file is PDF
        validate_pdf_file(file)
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        max_size_bytes = config.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {config.MAX_FILE_SIZE_MB}MB"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Generate unique document ID and S3 key
        document_id = str(uuid.uuid4())
        s3_key = f"users/{user_id}/documents/{document_id}/original.pdf"
        
        # Get S3 client
        s3_client = get_s3_client()
        
        # Upload to S3 with encryption
        try:
            s3_client.put_object(
                Bucket=config.S3_BUCKET_NAME,
                Key=s3_key,
                Body=file_content,
                ContentType='application/pdf',
                ServerSideEncryption='AES256',
                Metadata={'original_filename': file.filename}
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchBucket':
                raise HTTPException(
                    status_code=500,
                    detail=f"S3 bucket '{config.S3_BUCKET_NAME}' does not exist. Please run aws_setup.py first."
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload to S3: {str(e)}"
                )
        
        # Store metadata in DynamoDB
        try:
            dynamodb = get_dynamodb_resource()
            table = dynamodb.Table(config.DYNAMODB_DOCUMENTS_TABLE)
            
            item = {
                'PK': f'USER#{user_id}',
                'SK': f'DOC#{document_id}',
                'document_id': document_id,
                'user_id': user_id,
                'filename': file.filename,
                's3_key': s3_key,
                'uploaded_at': datetime.utcnow().isoformat(),
                'file_size': file_size,
                'processing_status': 'pending',
                'GSI1PK': f'DOC#{document_id}',
                'GSI1SK': 'METADATA'
            }
            
            table.put_item(Item=item)
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'ResourceNotFoundException':
                raise HTTPException(
                    status_code=500,
                    detail=f"DynamoDB table '{config.DYNAMODB_DOCUMENTS_TABLE}' does not exist. Please run aws_setup.py first."
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to store metadata: {str(e)}"
                )
        
        # Construct S3 URI
        s3_uri = f"s3://{config.S3_BUCKET_NAME}/{s3_key}"
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=file_size,
            status="success",
            message="Document uploaded successfully",
            s3_uri=s3_uri
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during upload: {str(e)}"
        )


def get_user_documents(user_id: str) -> DocumentListResponse:
    """
    Retrieve all documents for a user with error handling.
    """
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMODB_DOCUMENTS_TABLE)
        
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':pk': f'USER#{user_id}',
                ':sk': 'DOC#'
            }
        )
        
        documents = []
        for item in response.get('Items', []):
            documents.append(DocumentMetadata(
                document_id=item['document_id'],
                user_id=item['user_id'],
                filename=item['filename'],
                s3_key=item['s3_key'],
                uploaded_at=item['uploaded_at'],
                file_size=item['file_size'],
                processing_status=item.get('processing_status', 'pending')
            ))
        
        return DocumentListResponse(
            documents=documents,
            total=len(documents)
        )
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            raise HTTPException(
                status_code=500,
                detail=f"DynamoDB table '{config.DYNAMODB_DOCUMENTS_TABLE}' does not exist. Please run aws_setup.py first."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve documents: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error retrieving documents: {str(e)}"
        )
