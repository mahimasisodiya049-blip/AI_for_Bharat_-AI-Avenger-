"""
KiroFeed API - Multilingual Document Assistant
FastAPI backend with robust error handling for AWS and AI integrations.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from botocore.exceptions import NoCredentialsError, ClientError
import logging

# Import routers
from routes.auth_routes import router as auth_router
from routes.document_routes import router as document_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="KiroFeed API",
    version="1.0.0",
    description="Multilingual Document Assistant powered by AWS and AI"
)

# ============================================================================
# CORS Configuration - Allow frontend to communicate with backend
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js development server
        "http://127.0.0.1:3000",
        "*"  # Allow all origins (restrict in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# ============================================================================
# Global Exception Handlers - Prevent server crashes
# ============================================================================

@app.exception_handler(NoCredentialsError)
async def aws_credentials_exception_handler(request: Request, exc: NoCredentialsError):
    """Handle missing AWS credentials gracefully."""
    logger.error(f"AWS credentials error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "AWS credentials not found. Please check your environment variables.",
            "error_type": "AWS_CREDENTIALS_ERROR",
            "hint": "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file"
        }
    )


@app.exception_handler(ClientError)
async def aws_client_exception_handler(request: Request, exc: ClientError):
    """Handle AWS service errors (Bedrock, S3, DynamoDB, etc.)."""
    error_code = exc.response.get('Error', {}).get('Code', 'Unknown')
    error_message = exc.response.get('Error', {}).get('Message', str(exc))
    
    logger.error(f"AWS ClientError [{error_code}]: {error_message}")
    
    # Handle specific AWS error codes
    if error_code == 'ThrottlingException':
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "AWS service rate limit exceeded. Please try again in a moment.",
                "error_type": "THROTTLING_ERROR"
            }
        )
    elif error_code == 'AccessDeniedException':
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": "Access denied to AWS service. Please check your IAM permissions.",
                "error_type": "ACCESS_DENIED",
                "hint": "Ensure your AWS user has permissions for Bedrock, S3, DynamoDB, and Cognito"
            }
        )
    elif error_code == 'ResourceNotFoundException':
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": "AWS resource not found. Please ensure all services are set up.",
                "error_type": "RESOURCE_NOT_FOUND",
                "hint": "Run 'python aws_setup.py' to create required AWS resources"
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": f"AWS service error: {error_message}",
                "error_type": "AWS_SERVICE_ERROR",
                "error_code": error_code
            }
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Invalid request data",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "error_type": "INTERNAL_SERVER_ERROR"
        }
    )


# ============================================================================
# Include Routers - Register all API endpoints
# ============================================================================
app.include_router(auth_router)
app.include_router(document_router)


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/", tags=["health"])
async def root():
    """Root endpoint - API status check."""
    return {
        "message": "KiroFeed API is running",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "auth": "/auth",
            "documents": "/documents",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "service": "KiroFeed API",
        "version": "1.0.0"
    }


# ============================================================================
# Application Startup
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("=" * 60)
    logger.info("KiroFeed API Starting...")
    logger.info("=" * 60)
    logger.info("API Documentation: http://localhost:8000/docs")
    logger.info("Health Check: http://localhost:8000/health")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
