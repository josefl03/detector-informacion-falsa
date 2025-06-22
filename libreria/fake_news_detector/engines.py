from typing import List, Dict
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_result

import fake_news_detector.services.search as search
import fake_news_detector.debug as debug

MAX_RESULTS_PER_ENGINE = 8

class MultiSearchEngine:
    def __init__(self, engines: List["search.SearchEngine"]):
        self.engines = engines

    def multi_search(self, query, stop=None):
        results: List["search.SearchResult"] = []
        
        for engine in self.engines:
            results.extend(engine.search(query, max_results=MAX_RESULTS_PER_ENGINE))
            
            if stop and len(results) >= stop:
                break
            
        # Search for duplicates
        results = self.remove_duplicates(results)
        
        return results
    
    def remove_duplicates(self, results: List["search.SearchResult"]) -> List["search.SearchResult"]:
        seen = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen:
                seen.add(result.url)
                unique_results.append(result)
                
        return unique_results
    
if __name__ == "__main__":
    debug.setup()
    
    # Example usage
    engines = [search.BraveSearchEngine()]
    multi_engine = MultiSearchEngine(engines)
        
    def test_remove_duplicates():
        results = [
            search.SearchResult("http://example.com/1", "Title 1", "Description 1"),
            search.SearchResult("http://example.com/2", "Title 2", "Description 2"),
            search.SearchResult("http://example.com/1", "Title 3", "Description 3"),  # Duplicate
        ]
        logger.debug(f"Results: {results}")
        
        unique_results = multi_engine.remove_duplicates(results)
        logger.debug(f"Unique Results: {unique_results}")
        assert len(unique_results) == 2, "Duplicates were not removed correctly"
        assert unique_results[0].url == "http://example.com/1"
        assert unique_results[1].url == "http://example.com/2"
    test_remove_duplicates()