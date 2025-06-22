from waybackpy import WaybackMachineCDXServerAPI
from loguru import logger

import fake_news_detector.debug as debug
import fake_news_detector.network as network
import fake_news_detector.utils as utils

class Archive:
    def __init__(self):
        pass
    
    def get_archive(self, url: str) -> str | None:
        """
        Get the archive URL for a given URL using the Wayback Machine CDX Server API.
        
        Args:
            url (str): The URL to be archived.
            
        Returns:
            str: The archive URL if available, None otherwise.
        """
        cdx_api = WaybackMachineCDXServerAPI(url, network.get_useragent())
        oldest = cdx_api.oldest()
        
        logger.trace(oldest)
        
        logger.debug(f"Recovered URL on {utils.readable_datetime(oldest.datetime_timestamp)}: {oldest.archive_url}")
        
        return oldest.archive_url
        
if __name__ == "__main__":
    debug.setup()
    
    url = "http://foxnews.es/judd-nelson-found-dead-los-angeles-condo.html"
    
    archive = Archive()
    archv_url = archive.get_archive(url)
    print(archv_url)