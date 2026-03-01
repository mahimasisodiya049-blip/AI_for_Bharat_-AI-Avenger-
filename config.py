import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AWS Configuration
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    # S3 Configuration
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "kirofeed-documents")
    
    # DynamoDB Tables
    DYNAMODB_USERS_TABLE = os.getenv("DYNAMODB_USERS_TABLE", "KiroFeed-Users")
    DYNAMODB_DOCUMENTS_TABLE = os.getenv("DYNAMODB_DOCUMENTS_TABLE", "KiroFeed-Documents")
    DYNAMODB_SESSIONS_TABLE = os.getenv("DYNAMODB_SESSIONS_TABLE", "KiroFeed-ChatSessions")
    DYNAMODB_MESSAGES_TABLE = os.getenv("DYNAMODB_MESSAGES_TABLE", "KiroFeed-Messages")
    
    # Cognito Configuration
    COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
    COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
    COGNITO_REGION = os.getenv("COGNITO_REGION", "us-east-1")
    
    # Bedrock Configuration
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
    BEDROCK_EMBEDDING_MODEL_ID = os.getenv("BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v1")
    
    # Bhashini API
    BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY")
    BHASHINI_API_URL = os.getenv("BHASHINI_API_URL", "https://api.bhashini.gov.in")
    
    # Application Settings
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

config = Config()
