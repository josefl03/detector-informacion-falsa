from abc import ABC, abstractmethod
import os
import random
import asyncio
from loguru import logger
import dateparser
import urllib.parse
import datetime
import time
from dataclasses import dataclass, field
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_result

import brave_search_python_client

import fake_news_detector.debug as debug
import fake_news_detector.utils as utils
from fake_news_detector.datatypes import *

FULL_SEARCH = True

class SearchEngine(ABC):
    @abstractmethod
    def search(self, query: str, max_results: int = None):
        pass
    
class BraveSearchEngine(SearchEngine):
    
    DEFAULT_DELAY = 1 # seconds
    
    def __init__(self):
        self.client = brave_search_python_client.BraveSearch(api_key=os.getenv("BRAVE_SEARCH_API_KEY"))
    
    #TODO: Retry only in page error
    @retry(stop=stop_after_attempt(3),wait=wait_fixed(2), \
           retry=retry_if_result(lambda results: results is []))
    def search(self, query: str, max_results: int = None):
        results = []
        
        # Pagination from 0 to 9
        for i in range(0, 10):
            logger.debug(f"Searching page {i} with {self.__class__.__name__}")
            
            response = asyncio.run(
                self.client.web(brave_search_python_client.WebSearchRequest(
                    q=query,
                    count=20, # 20 max
                    offset=i, # 9 max
                    
                    spellcheck=False,
                    safe_search=brave_search_python_client.NewsSafeSearchType.off,
                    
                    # Language and country
                    country=brave_search_python_client.CountryCode.ES,
                    search_lang=brave_search_python_client.LanguageCode.ES,
                    
                    # Optional: freshness
                    #freshness=brave_search_python_client.FreshnessType.pd,
                ))
            )
            
            if not response.web or not response.web.results:
                # Finished searching
                logger.debug(f"No more results found after {i} pages.")
                break
            
            results_raw = response.web.results
            logger.debug(f"Found {len(results_raw)} results.")
            
            for result in results_raw:
                # Get the url without parameters
                url_clean = utils.clean_url(result.url)
                
                if url_clean in [r.url for r in results]:
                    continue
                
                logger.debug(f"[{len(results)}] Found: {url_clean}")
                
                # Convert the age (X days ago..) to a datetime object
                dt = None
                if result.age:
                    dt = dateparser.parse(result.age)
                    dt.replace(hour=0, minute=0, second=0, microsecond=0) # Remove time (unknown)
                    
                logger.trace(f"[{len(results)}] ({utils.readable_datetime(dt)}) {result.title}")
                
                # Append the result to the list
                results.append(SearchResult(
                    url=url_clean,
                    title=result.title,
                    #description=result.description,
                    date=dt,
                    #thumbnail=result.thumbnail
                ))
            
            # Limit search results
            if not FULL_SEARCH:
                # Get only the first page
                break
            
            if max_results and len(results) > max_results:
                logger.debug(f"Reached max results: {max_results}")
                break
            
            time.sleep(self.DEFAULT_DELAY) # Avoid rate limit
        
        
        return results
    
if __name__ == "__main__":
    debug.setup()
    
    # Test search
    engine = BraveSearchEngine()
    
    logger.info("Searching...")
    
    results = engine.search("pedro sanchez dana")
    
    logger.info(f"Found: {len(results)}")
    for result in results:
        logger.info(result.url)
        
        
    