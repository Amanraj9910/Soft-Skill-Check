"""
Configure optimal thread pool size for handling concurrent users.
Run this before starting the backend server for production.
"""
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

# Configuration
THREAD_POOL_SIZE = int(os.getenv('ASYNCIO_THREAD_POOL_SIZE', '100'))  # Default 100 for 40+ users

def configure_thread_pool():
    """Increase default thread pool size for better concurrency."""
    
    loop = asyncio.get_event_loop()
    
    # Create executor with more threads
    executor = ThreadPoolExecutor(
        max_workers=THREAD_POOL_SIZE,
        thread_name_prefix='speech_worker'
    )
    
    # Set as default executor
    loop.set_default_executor(executor)
    
    print(f"✅ Thread pool configured: {THREAD_POOL_SIZE} workers")
    print(f"ℹ️  This allows handling {THREAD_POOL_SIZE // 2}+ concurrent transcription requests")
    
    return executor

if __name__ == "__main__":
    executor = configure_thread_pool()
    
    # Show current configuration
    import threading
    print(f"\n📊 Current thread count: {threading.active_count()}")
    print(f"🎯 Max recommended concurrent users: {THREAD_POOL_SIZE // 2}")
    print(f"\n💡 To change thread pool size:")
    print(f"   Set environment variable: ASYNCIO_THREAD_POOL_SIZE=200")
    print(f"   Then restart the backend server")
