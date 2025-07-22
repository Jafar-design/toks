"""
Retry utilities for handling HTTP errors and network failures.
"""

import time
import logging
from typing import Callable, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests


logger = logging.getLogger(__name__)


class HTTPRetryError(Exception):
    """Custom exception for HTTP retry failures."""
    pass


def is_5xx_error(exception):
    """Check if exception is a 5xx HTTP error."""
    if isinstance(exception, requests.HTTPError):
        return exception.response.status_code >= 500
    return False


def retry_on_5xx(max_attempts: int = 3, min_wait: float = 1.0, max_wait: float = 10.0):
    """
    Decorator for retrying HTTP requests on 5xx errors.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(requests.HTTPError) & retry_if_exception_type(requests.RequestException),
        reraise=True
    )


class RetryableHTTPSession:
    """HTTP session with built-in 5xx retry logic."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.0):
        self.session = requests.Session()
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
    def get(self, url: str, **kwargs) -> requests.Response:
        """GET request with retry logic."""
        return self._request_with_retry('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """POST request with retry logic."""
        return self._request_with_retry('POST', url, **kwargs)
    
    def _request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """Execute HTTP request with retry logic on 5xx errors."""
        last_exception = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.request(method, url, **kwargs)
                
                # Check for 5xx errors
                if response.status_code >= 500:
                    logger.warning(
                        f"HTTP {response.status_code} error on attempt {attempt}/{self.max_retries} "
                        f"for {method} {url}"
                    )
                    
                    if attempt < self.max_retries:
                        wait_time = self.backoff_factor * (2 ** (attempt - 1))
                        logger.info(f"Retrying in {wait_time:.1f} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        response.raise_for_status()
                
                # Success or 4xx error (don't retry)
                return response
                
            except requests.RequestException as e:
                last_exception = e
                logger.error(f"Request failed on attempt {attempt}/{self.max_retries}: {e}")
                
                if attempt < self.max_retries:
                    wait_time = self.backoff_factor * (2 ** (attempt - 1))
                    logger.info(f"Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    raise HTTPRetryError(f"Max retries ({self.max_retries}) exceeded") from e
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception