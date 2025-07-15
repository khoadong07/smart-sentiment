from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional
import asyncio
import hashlib
import json
import time
from app.core import filter_negative_content

# Initialize FastAPI app
app = FastAPI(
    title="Negative Content Filter API",
    description="API for filtering negative content with caching",
    version="1.0.0"
)

# --- Models ---

class ErrorResponse(BaseModel):
    """Standard error response model"""
    detail: str

class CacheStats(BaseModel):
    """Cache statistics model"""
    cache_size: int
    max_size: int
    ttl: int
    usage_percent: float

class FilterItem(BaseModel):
    """Input model for filtering negative content"""
    id: Optional[str] = None
    topic_name: Optional[str] = None
    type: Optional[str] = None
    topic_id: Optional[str] = None
    site_id: Optional[str] = None
    site_name: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    is_kol: Optional[bool] = False
    total_interactions: Optional[int] = None

    model_config = ConfigDict(
        extra="forbid",  # Prevent extra fields
        str_strip_whitespace=True  # Strip whitespace from strings
    )

class BatchFilterRequest(BaseModel):
    """Request model for batch filtering"""
    data: List[FilterItem]

    model_config = ConfigDict(
        extra="forbid"
    )

class FilterResponse(BaseModel):
    """Response model for filtered content"""
    id: str
    topic_name: str
    type: str
    topic_id: str
    site_id: str
    site_name: str
    contains_topic: bool
    targeting_topic: bool
    crisis_keywords: List[str]
    log_level: int
    reason: str

# --- Cache Manager ---

class FilterCache:
    """Cache manager for negative content filtering results"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        Initialize cache with size and TTL constraints.
        
        Args:
            max_size: Maximum number of items in cache
            ttl: Time to live (seconds) for cache entries
        """
        self.cache: Dict[str, Any] = {}
        self.max_size: int = max_size
        self.ttl: int = ttl
        self.access_times: Dict[str, float] = {}

    def _generate_cache_key(self, data_input: Dict[str, Any]) -> str:
        """Generate cache key from input data"""
        cache_fields = {
            'title': data_input.get('title', ''),
            'content': data_input.get('content', ''),
            'description': data_input.get('description', ''),
            'topic_name': data_input.get('topic_name', ''),
            'site_name': data_input.get('site_name', ''),
            'type': data_input.get('type', '')
        }
        cache_str = json.dumps(cache_fields, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(cache_str.encode('utf-8')).hexdigest()

    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry has expired"""
        return time.time() - timestamp > self.ttl

    def _cleanup_expired(self) -> None:
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self.access_times.items()
            if current_time - timestamp > self.ttl
        ]
        for key in expired_keys:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)

    def _evict_lru(self) -> None:
        """Evict least recently used entry when cache is full"""
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times, key=self.access_times.get)
            self.cache.pop(oldest_key, None)
            self.access_times.pop(oldest_key, None)

    def get(self, data_input: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve result from cache"""
        cache_key = self._generate_cache_key(data_input)
        if cache_key in self.cache:
            if self._is_expired(self.access_times[cache_key]):
                self.cache.pop(cache_key, None)
                self.access_times.pop(cache_key, None)
                return None
            self.access_times[cache_key] = time.time()
            return self.cache[cache_key]
        return None

    def set(self, data_input: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Store result in cache"""
        self._cleanup_expired()
        self._evict_lru()
        cache_key = self._generate_cache_key(data_input)
        self.cache[cache_key] = result.copy()
        self.access_times[cache_key] = time.time()

    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.access_times.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'ttl': self.ttl,
            'usage_percent': len(self.cache) / self.max_size * 100
        }

# Initialize global cache
filter_cache = FilterCache(max_size=1000, ttl=3600)

# --- Services ---

async def filter_negative_content_service(data_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter negative content for a single item with caching.
    
    Args:
        data_input: Input data to filter
        
    Returns:
        Dictionary containing input fields and filter results
    """
    cached_result = filter_cache.get(data_input)
    if cached_result:
        print(f"📋 Cache hit for item: {data_input.get('id', 'unknown')}")
        return cached_result

    print(f"🔍 Processing item: {data_input.get('id', 'unknown')}")
    result = {
        "id": data_input.get("id", ""),
        "topic_name": data_input.get("topic_name", ""),
        "type": data_input.get("type", ""),
        "topic_id": data_input.get("topic_id", ""),
        "site_id": data_input.get("site_id", ""),
        "site_name": data_input.get("site_name", ""),
        "contains_topic": False,
        "targeting_topic": False,
        "crisis_keywords": [],
        "log_level": 2,
        "reason": ""
    }

    try:
        filter_result = await filter_negative_content(data_input, {
            "contains_topic": False,
            "targeting_topic": False,
            "crisis_keywords": [],
            "log_level": 2,
            "reason": ""
        })
        result.update(filter_result)
        filter_cache.set(data_input, result)
        return result
    except Exception as e:
        print(f"❌ Error processing item {data_input.get('id', 'unknown')}: {e}")
        result["reason"] = f"Error processing item: {str(e)}"
        return result

async def batch_filter_negative_content_service(data_list: List[FilterItem]) -> List[Dict[str, Any]]:
    """
    Filter negative content for multiple items concurrently.
    
    Args:
        data_list: List of items to filter
        
    Returns:
        List of dictionaries containing input fields and filter results
    """
    print(f"🚀 Processing batch of {len(data_list)} items")
    tasks = [filter_negative_content_service(item.dict(exclude_none=True)) for item in data_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    processed_results = []
    for i, (item, result) in enumerate(zip(data_list, results)):
        default_result = {
            "id": item.id or "",
            "topic_name": item.topic_name or "",
            "type": item.type or "",
            "topic_id": item.topic_id or "",
            "site_id": item.site_id or "",
            "site_name": item.site_name or "",
            "contains_topic": False,
            "targeting_topic": False,
            "crisis_keywords": [],
            "log_level": 2,
            "reason": ""
        }
        if isinstance(result, Exception):
            print(f"❌ Error in batch item {i}: {result}")
            default_result["reason"] = f"Error processing item: {str(result)}"
            processed_results.append(default_result)
        else:
            processed_results.append(result)
    
    return processed_results

# --- Routes ---

@app.post(
    "/api/v1/filter/negative-content",
    response_model=FilterResponse,
    tags=["Filter"],
    summary="Filter single item for negative content",
    responses={500: {"model": ErrorResponse}}
)
async def filter_single_negative_content(item: FilterItem):
    """
    Filter a single item for negative content.
    
    Returns filter results including input fields and analysis.
    """
    try:
        result = await filter_negative_content_service(item.dict(exclude_none=True))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing item: {str(e)}")

@app.post(
    "/api/v1/filter/negative-content/batch",
    response_model=List[FilterResponse],
    tags=["Filter"],
    summary="Filter multiple items for negative content",
    responses={500: {"model": ErrorResponse}}
)
async def filter_batch_negative_content(request: BatchFilterRequest):
    """
    Filter multiple items for negative content concurrently.
    
    Returns list of filter results including input fields and analysis.
    """
    try:
        results = await batch_filter_negative_content_service(request.data)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")

@app.get(
    "/api/v1/cache/stats",
    response_model=CacheStats,
    tags=["Cache"],
    summary="Get cache statistics"
)
async def get_cache_stats():
    """Retrieve current cache statistics."""
    return filter_cache.get_stats()

@app.delete(
    "/api/v1/cache",
    tags=["Cache"],
    summary="Clear cache",
    responses={200: {"model": Dict[str, str]}}
)
async def clear_cache():
    """Clear all cache entries."""
    filter_cache.clear()
    return {"message": "Cache cleared successfully"}

# --- Main ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)