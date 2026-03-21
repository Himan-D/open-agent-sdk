"""Storage - Database tools and integrations.

Supports:
- PostgreSQL with asyncpg
- MongoDB with motor
- Redis with redis-py
- S3 with boto3
- File storage
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class DatabaseConfig:
    """Configuration for database connections."""
    host: str = "localhost"
    port: int = 5432
    database: str = "smithai"
    user: str = "postgres"
    password: str = ""
    min_connections: int = 1
    max_connections: int = 10


@dataclass
class RedisConfig:
    """Configuration for Redis."""
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    ssl: bool = False


@dataclass
class MongoConfig:
    """Configuration for MongoDB."""
    host: str = "localhost"
    port: int = 27017
    database: str = "smithai"
    user: str = ""
    password: str = ""


class PostgresTool:
    """PostgreSQL database operations.
    
    Real use cases:
    - Store agent conversation history
    - Query structured business data
    - Transactional operations
    - Analytics queries
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._pool = None
    
    async def connect(self):
        """Connect to PostgreSQL."""
        try:
            import asyncpg
            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
            )
            logger.info("postgres_connected", host=self.config.host, database=self.config.database)
        except ImportError:
            raise ImportError("asyncpg not installed. Run: pip install asyncpg")
    
    async def close(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query."""
        if not self._pool:
            await self.connect()
        
        async with self._pool.acquire() as conn:
            result = await conn.execute(query, *args)
            return result
    
    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch rows as dictionaries."""
        if not self._pool:
            await self.connect()
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch single row."""
        rows = await self.fetch(query, *args)
        return rows[0] if rows else None
    
    async def fetchval(self, query: str, *args) -> Any:
        """Fetch single value."""
        if not self._pool:
            await self.connect()
        
        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def create_tables(self):
        """Create necessary tables."""
        await self.execute("""
            CREATE TABLE IF NOT EXISTS agent_sessions (
                id UUID PRIMARY KEY,
                agent_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                metadata JSONB
            )
        """)
        
        await self.execute("""
            CREATE TABLE IF NOT EXISTS agent_messages (
                id UUID PRIMARY KEY,
                session_id UUID REFERENCES agent_sessions(id),
                role VARCHAR(50),
                content TEXT,
                tool_calls JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        await self.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session 
            ON agent_messages(session_id, created_at)
        """)


class MongoTool:
    """MongoDB database operations.
    
    Real use cases:
    - Store unstructured data
    - Document storage
    - Flexible schemas
    - Geospatial queries
    """
    
    def __init__(self, config: Optional[MongoConfig] = None):
        self.config = config or MongoConfig()
        self._client = None
        self._db = None
    
    async def connect(self):
        """Connect to MongoDB."""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            
            uri = f"mongodb://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}" \
                if self.config.user else \
                f"mongodb://{self.config.host}:{self.config.port}"
            
            self._client = AsyncIOMotorClient(uri)
            self._db = self._client[self.config.database]
            logger.info("mongodb_connected", host=self.config.host, database=self.config.database)
        except ImportError:
            raise ImportError("motor not installed. Run: pip install motor")
    
    async def close(self):
        """Close connection."""
        if self._client:
            self._client.close()
    
    @property
    def db(self):
        if not self._db:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._db
    
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert a single document."""
        result = await self.db[collection].insert_one(document)
        return str(result.inserted_id)
    
    async def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents."""
        result = await self.db[collection].insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    async def find_one(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Find a single document."""
        doc = await self.db[collection].find_one(query, projection)
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
    
    async def find(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Tuple[str, int]]] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """Find documents."""
        cursor = self.db[collection].find(query, projection)
        
        if sort:
            cursor = cursor.sort(sort)
        
        cursor = cursor.skip(skip).limit(limit)
        
        documents = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            documents.append(doc)
        
        return documents
    
    async def update_one(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
    ) -> int:
        """Update a single document."""
        result = await self.db[collection].update_one(query, {"$set": update})
        return result.modified_count
    
    async def update_many(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
    ) -> int:
        """Update multiple documents."""
        result = await self.db[collection].update_many(query, {"$set": update})
        return result.modified_count
    
    async def delete_one(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete a single document."""
        result = await self.db[collection].delete_one(query)
        return result.deleted_count
    
    async def delete_many(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete multiple documents."""
        result = await self.db[collection].delete_many(query)
        return result.deleted_count
    
    async def count(self, collection: str, query: Dict[str, Any] = None) -> int:
        """Count documents."""
        return await self.db[collection].count_documents(query or {})
    
    async def aggregate(self, collection: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run aggregation pipeline."""
        cursor = self.db[collection].aggregate(pipeline)
        return await cursor.to_list(length=None)


class RedisTool:
    """Redis operations.
    
    Real use cases:
    - Cache agent responses
    - Pub/sub messaging
    - Rate limiting
    - Session storage
    - Real-time data
    """
    
    def __init__(self, config: Optional[RedisConfig] = None):
        self.config = config or RedisConfig()
        self._client = None
    
    async def connect(self):
        """Connect to Redis."""
        try:
            import redis.asyncio as redis
            
            self._client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password if self.config.password else None,
                db=self.config.db,
                ssl=self.config.ssl,
                decode_responses=True,
            )
            await self._client.ping()
            logger.info("redis_connected", host=self.config.host)
        except ImportError:
            raise ImportError("redis not installed. Run: pip install redis")
    
    async def close(self):
        """Close connection."""
        if self._client:
            await self._client.close()
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value."""
        if not self._client:
            await self.connect()
        return await self._client.get(key)
    
    async def set(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None,
        px: Optional[int] = None,
    ) -> bool:
        """Set a value with optional expiry."""
        if not self._client:
            await self.connect()
        return await self._client.set(key, value, ex=ex, px=px)
    
    async def delete(self, key: str) -> int:
        """Delete a key."""
        if not self._client:
            await self.connect()
        return await self._client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self._client:
            await self.connect()
        return await self._client.exists(key) > 0
    
    async def incr(self, key: str) -> int:
        """Increment a counter."""
        if not self._client:
            await self.connect()
        return await self._client.incr(key)
    
    async def decr(self, key: str) -> int:
        """Decrement a counter."""
        if not self._client:
            await self.connect()
        return await self._client.decr(key)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiry on a key."""
        if not self._client:
            await self.connect()
        return await self._client.expire(key, seconds)
    
    async def ttl(self, key: str) -> int:
        """Get time to live."""
        if not self._client:
            await self.connect()
        return await self._client.ttl(key)
    
    async def lpush(self, key: str, *values: str) -> int:
        """Push to list."""
        if not self._client:
            await self.connect()
        return await self._client.lpush(key, *values)
    
    async def rpop(self, key: str) -> Optional[str]:
        """Pop from list."""
        if not self._client:
            await self.connect()
        return await self._client.rpop(key)
    
    async def llen(self, key: str) -> int:
        """Get list length."""
        if not self._client:
            await self.connect()
        return await self._client.llen(key)
    
    async def hset(self, key: str, field: str, value: str) -> int:
        """Set hash field."""
        if not self._client:
            await self.connect()
        return await self._client.hset(key, field, value)
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field."""
        if not self._client:
            await self.connect()
        return await self._client.hget(key, field)
    
    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields."""
        if not self._client:
            await self.connect()
        return await self._client.hgetall(key)
    
    async def publish(self, channel: str, message: str) -> int:
        """Publish to channel."""
        if not self._client:
            await self.connect()
        return await self._client.publish(channel, message)
    
    def subscribe(self, *channels: str):
        """Subscribe to channels."""
        if not self._client:
            import redis.asyncio as redis
            self._client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                decode_responses=True,
            )
        return self._client.pubsub().subscribe(*channels)


class S3Tool:
    """AWS S3 storage operations.
    
    Real use cases:
    - Store agent artifacts
    - Backup data
    - Share files across services
    """
    
    def __init__(
        self,
        bucket: str = "smithai-storage",
        region: str = "us-east-1",
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
    ):
        self.bucket = bucket
        self.region = region
        self._client = None
        
        self._access_key = access_key or os.environ.get("AWS_ACCESS_KEY_ID")
        self._secret_key = secret_key or os.environ.get("AWS_SECRET_ACCESS_KEY")
    
    def _ensure_client(self):
        """Ensure S3 client is initialized."""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    "s3",
                    region_name=self.region,
                    aws_access_key_id=self._access_key,
                    aws_secret_access_key=self._secret_key,
                )
            except ImportError:
                raise ImportError("boto3 not installed. Run: pip install boto3")
    
    async def upload_file(self, key: str, file_path: str, content_type: str = "application/octet-stream") -> str:
        """Upload a file."""
        self._ensure_client()
        import botocore.exceptions
        
        try:
            self._client.upload_file(
                file_path,
                self.bucket,
                key,
                ExtraArgs={"ContentType": content_type}
            )
            return f"s3://{self.bucket}/{key}"
        except botocore.exceptions.ClientError as e:
            logger.error("s3_upload_failed", key=key, error=str(e))
            raise
    
    async def upload_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload bytes directly."""
        self._ensure_client()
        
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type
        )
        return f"s3://{self.bucket}/{key}"
    
    async def download_file(self, key: str, file_path: str) -> None:
        """Download a file."""
        self._ensure_client()
        
        self._client.download_file(self.bucket, key, file_path)
    
    async def download_bytes(self, key: str) -> bytes:
        """Download as bytes."""
        self._ensure_client()
        
        response = self._client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()
    
    async def list_files(self, prefix: str = "") -> List[str]:
        """List files with prefix."""
        self._ensure_client()
        
        response = self._client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        return [obj["Key"] for obj in response.get("Contents", [])]
    
    async def delete_file(self, key: str) -> None:
        """Delete a file."""
        self._ensure_client()
        self._client.delete_object(Bucket=self.bucket, Key=key)
    
    async def get_url(self, key: str, expires: int = 3600) -> str:
        """Get presigned URL."""
        self._ensure_client()
        
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires
        )


class GCSStorage:
    """Google Cloud Storage operations."""
    
    def __init__(self, bucket: str = "smithai-storage", project: Optional[str] = None):
        self.bucket = bucket
        self.project = project or os.environ.get("GCP_PROJECT")
        self._client = None
    
    def _ensure_client(self):
        """Ensure GCS client is initialized."""
        if self._client is None:
            try:
                from google.cloud import storage
                self._client = storage.Client(project=self.project)
            except ImportError:
                raise ImportError("google-cloud-storage not installed")
    
    async def upload_file(self, key: str, file_path: str, content_type: str = "application/octet-stream") -> str:
        """Upload a file."""
        self._ensure_client()
        
        bucket = self._client.bucket(self.bucket)
        blob = bucket.blob(key)
        blob.upload_from_filename(file_path, content_type=content_type)
        return f"gs://{self.bucket}/{key}"
    
    async def download_file(self, key: str, file_path: str) -> None:
        """Download a file."""
        self._ensure_client()
        
        bucket = self._client.bucket(self.bucket)
        blob = bucket.blob(key)
        blob.download_to_filename(file_path)
    
    async def list_files(self, prefix: str = "") -> List[str]:
        """List files with prefix."""
        self._ensure_client()
        
        bucket = self._client.bucket(self.bucket)
        blobs = bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]


__all__ = [
    "DatabaseConfig",
    "RedisConfig",
    "MongoConfig",
    "PostgresTool",
    "MongoTool",
    "RedisTool",
    "S3Tool",
    "GCSStorage",
]
