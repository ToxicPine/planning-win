import logging
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from pathlib import Path
from typing import Optional, Union, Dict, Any, Literal, Callable, Awaitable
import aiohttp

from .result import Result, create_success, create_failure
from .util import with_exponential_backoff
from .environment import EnvSettings, load_env_config
from pydantic import BaseModel

# Default download directory path
DEFAULT_DOWNLOAD_DIR_PATH = Path.home() / ".splitup" / "objects"
DEFAULT_DOWNLOAD_DIR = str(DEFAULT_DOWNLOAD_DIR_PATH.absolute())


class StorageConfig(BaseModel):
    """Storage configuration model."""

    SPLITUP_STORAGE_API_ENDPOINT: str
    SPLITUP_STORAGE_API_KEY: str
    SPLITUP_STORAGE_REGION: str
    SPLITUP_STORAGE_S3_BUCKET: str


class S3ClientFactory:
    """Factory for creating S3 clients."""

    @staticmethod
    def create_client(endpoint_url: str, region: str, api_key: Optional[str] = None):
        """Create and return a new S3 client instance."""
        return boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint_url,
            config=Config(signature_version="s3v4", region_name=region),
        )


class DownloadManager:
    """Handles file downloads from URLs."""

    def __init__(self, download_dir: Path, logger: logging.Logger):
        self.download_dir = download_dir
        self.logger = logger

    async def download_from_url(
        self, url: str, local_filename: Optional[str] = None
    ) -> Result[Path, str]:
        """
        Download a file from a URL with exponential backoff.

        Args:
            url: URL to download from
            local_filename: Optional local filename, defaults to the URL's basename

        Returns:
            Result containing the local file path or an error message
        """
        if not local_filename:
            local_filename = url.split("/")[-1]

        local_path = self.download_dir / local_filename

        async def download_operation() -> Result[Path, str]:
            try:
                self.logger.info(f"Downloading {url} to {local_path}")
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status != 200:
                            return create_failure(
                                f"HTTP Error {response.status}: {response.reason}"
                            )

                        content = await response.read()
                        local_path.write_bytes(content)

                return create_success(local_path)
            except aiohttp.ClientError as e:
                error_msg = f"HTTP Client Error: {str(e)}"
                self.logger.error(error_msg)
                return create_failure(error_msg)
            except Exception as e:
                error_msg = f"Unexpected Error Downloading {url}: {str(e)}"
                self.logger.error(error_msg)
                return create_failure(error_msg)

        return await with_exponential_backoff(
            download_operation,
            self.logger,
            f"Download: {url}",
            max_attempts=5,
            initial_backoff=1,
        )

    def is_downloaded(self, key: str) -> bool:
        """Check if an object has been downloaded."""
        return (self.download_dir / key).exists()


class S3Operations:
    """Handles S3-specific operations."""

    def __init__(self, s3_client, default_bucket: str, logger: logging.Logger):
        self.s3_client = s3_client
        self.default_bucket = default_bucket
        self.logger = logger

    async def generate_presigned_url(
        self,
        key: str,
        operation: Literal["upload", "download", "delete"] = "download",
        expires_in: int = 3600,
        bucket: Optional[str] = None,
    ) -> Result[str, str]:
        """
        Generate a presigned URL for S3 operations.

        Args:
            key: S3 object key
            operation: Type of operation (upload, download, delete)
            expires_in: Expiration time in seconds
            bucket: Optional S3 bucket name, defaults to configured bucket

        Returns:
            Result containing the presigned URL or an error message
        """
        if not self.s3_client:
            return create_failure("S3 client not initialized")

        # Use default bucket if not specified
        if not bucket:
            bucket = self.default_bucket

        try:
            self.logger.info(
                f"Generating Presigned URL for {operation} Operation on {bucket}/{key}"
            )

            if operation == "upload":
                client_method = "put_object"
            elif operation == "download":
                client_method = "get_object"
            elif operation == "delete":
                client_method = "delete_object"

            signed_url = self.s3_client.generate_presigned_url(
                client_method,
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )

            return create_success(signed_url)
        except ClientError as e:
            error_msg = f"S3 Client Error Generating Presigned URL: {str(e)}"
            self.logger.error(error_msg)
            return create_failure(error_msg)
        except Exception as e:
            error_msg = f"Unexpected Error Generating Presigned URL for {bucket}/{key}: {str(e)}"
            self.logger.error(error_msg)
            return create_failure(error_msg)

    async def put_object(
        self,
        key: str,
        file_path: Union[str, Path],
        metadata: Optional[Dict[str, str]] = None,
        bucket: Optional[str] = None,
    ) -> Result[str, str]:
        """
        Upload an object to S3 with exponential backoff.

        Args:
            key: S3 object key
            file_path: Path to the local file
            metadata: Optional metadata to attach to the object
            bucket: Optional S3 bucket name, defaults to configured bucket

        Returns:
            Result containing the S3 URI or an error message
        """
        if not self.s3_client:
            return create_failure("S3 Client Not Initialized")

        # Use default bucket if not specified
        if not bucket:
            if not self.default_bucket:
                return create_failure("S3 Bucket Not Configured")
            bucket = self.default_bucket

        file_path = Path(file_path)
        if not file_path.exists():
            return create_failure(f"File Not Found: {file_path}")

        extra_args: Dict[str, Any] = {}
        if metadata:
            extra_args["Metadata"] = metadata

        async def upload_operation() -> Result[str, str]:
            try:
                self.logger.info(f"Uploading {file_path} to {bucket}/{key}")
                self.s3_client.upload_file(
                    str(file_path), bucket, key, ExtraArgs=extra_args
                )
                return create_success(f"s3://{bucket}/{key}")
            except ClientError as e:
                error_msg = f"S3 Client Error: {str(e)}"
                self.logger.error(error_msg)
                return create_failure(error_msg)
            except Exception as e:
                error_msg = f"Unexpected Error Uploading to {bucket}/{key}: {str(e)}"
                self.logger.error(error_msg)
                return create_failure(error_msg)

        return await with_exponential_backoff(
            upload_operation,
            self.logger,
            f"Upload to {bucket}/{key}",
            max_attempts=5,
            initial_backoff=1,
        )


class StorageService:
    """Service for interacting with S3 and other storage backends."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.s3_client = None
        self.s3_operations = None
        self.download_manager = None

        self._init_storage()

    def _init_storage(self) -> None:
        """Initialize storage configuration."""
        env_result = load_env_config(EnvSettings)

        if env_result.status == "failure":
            self.logger.error(
                f"Failed to Load Storage Configuration: {env_result.error}"
            )
            raise Exception(f"Failed to Load Storage Configuration: {env_result.error}")
        else:
            storage_config = StorageConfig(
                SPLITUP_STORAGE_API_ENDPOINT=env_result.data.SPLITUP_STORAGE_API_ENDPOINT,
                SPLITUP_STORAGE_API_KEY=env_result.data.SPLITUP_STORAGE_API_KEY,
                SPLITUP_STORAGE_S3_BUCKET=env_result.data.SPLITUP_STORAGE_S3_BUCKET,
                SPLITUP_STORAGE_REGION=env_result.data.SPLITUP_STORAGE_REGION,
            )
            self.config = storage_config

        # Create download directory if it doesn't exist
        self.download_dir = DEFAULT_DOWNLOAD_DIR_PATH
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Initialize download manager
        self.download_manager = DownloadManager(self.download_dir, self.logger)

        # Initialize S3 client if endpoint is provided
        try:
            self.s3_client = S3ClientFactory.create_client(
                endpoint_url=self.config.SPLITUP_STORAGE_API_ENDPOINT,
                region=self.config.SPLITUP_STORAGE_REGION,
                api_key=self.config.SPLITUP_STORAGE_API_KEY,
            )
            self.s3_operations = S3Operations(
                self.s3_client, self.config.SPLITUP_STORAGE_S3_BUCKET, self.logger
            )
            self.logger.info(
                f"Initialized S3 Client with Endpoint: {self.config.SPLITUP_STORAGE_API_ENDPOINT}"
            )
        except Exception as e:
            self.logger.error(f"Failed to Initialize S3 Client: {str(e)}")

    async def get_object(
        self, key: str, local_filename: Optional[str] = None
    ) -> Result[Path, str]:
        """
        Download an object from S3 with exponential backoff.

        Args:
            key: S3 object key
            local_filename: Optional local filename, defaults to the key's basename

        Returns:
            Result containing the local file path or an error message
        """
        if not self.s3_operations:
            return create_failure("S3 Client Not Initialized")

        if not local_filename:
            local_filename = Path(key).name

        # Generate presigned URL and download using it
        url_result = await self.s3_operations.generate_presigned_url(key, "download")
        if url_result.status == "failure":
            return create_failure(
                f"Failed to Generate Presigned URL: {url_result.error}"
            )

        return await self.download_manager.download_from_url(
            url_result.data, local_filename
        )

    async def put_object(
        self,
        key: str,
        file_path: Union[str, Path],
        metadata: Optional[Dict[str, str]] = None,
        bucket: Optional[str] = None,
    ) -> Result[str, str]:
        """
        Upload an object to S3 with exponential backoff.

        Args:
            key: S3 object key
            file_path: Path to the local file
            metadata: Optional metadata to attach to the object
            bucket: Optional S3 bucket name, defaults to configured bucket

        Returns:
            Result containing the S3 URI or an error message
        """
        if not self.s3_operations:
            return create_failure("S3 Client Not Initialized")

        return await self.s3_operations.put_object(key, file_path, metadata, bucket)

    async def is_downloaded(self, key: str) -> Result[bool, str]:
        """Check if an object has been downloaded."""
        return await self.download_manager.is_downloaded(key)

    async def generate_presigned_url(
        self,
        key: str,
        operation: Literal["upload", "download", "delete"] = "download",
        expires_in: int = 3600,
        bucket: Optional[str] = None,
    ) -> Result[str, str]:
        """
        Generate a presigned URL for S3 operations.

        Args:
            key: S3 object key
            operation: Type of operation (upload, download, delete)
            expires_in: Expiration time in seconds
            bucket: Optional S3 bucket name, defaults to configured bucket

        Returns:
            Result containing the presigned URL or an error message
        """
        if not self.s3_operations:
            return create_failure("S3 Client Not Initialized")

        return await self.s3_operations.generate_presigned_url(
            key, operation, expires_in, bucket
        )

    async def download_from_url(
        self, url: str, local_filename: Optional[str] = None
    ) -> Result[Path, str]:
        """
        Download a file from a URL with exponential backoff.

        Args:
            url: URL to download from
            local_filename: Optional local filename, defaults to the URL's basename

        Returns:
            Result containing the local file path or an error message
        """
        return await self.download_manager.download_from_url(url, local_filename)
