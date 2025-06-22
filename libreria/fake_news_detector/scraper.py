from typing import List
from loguru import logger
from enum import Flag
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_result

import fake_news_detector.debug as debug
import fake_news_detector.services.web.archive as archive
import fake_news_detector.services.web.scrape as scrape
from fake_news_detector.services.web.scrape import Format
import fake_news_detector.utils as utils

SCRAPED_SIZE_LIMIT = 6000000  # ~4 MB limit for scraped content

class Scraper:
    archive: "archive.Archive"
    scrapers: List[scrape.Scraper]
    
    def __init__(self, scrapers: List[scrape.Scraper]):
        self.archive = archive.Archive()
        self.scrapers = scrapers
        
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1),
           retry=retry_if_result(lambda result: result is None),
           retry_error_callback=lambda retry_state: logger.error(f"Scraping failed after {retry_state.attempt_number} attempts."))
    def scrape(self, url: str, format: Format = Format.HTML) -> any:
        """
        Scrape the given URL using the available scrapers.
        
        Args:
            url (str): The URL to scrape.
            hard (bool): If True, use the hard mode to scrape (with JavaScript enabled).
        
        Returns:
            str: The scraped content.
        """
        logger.debug(f"Scraping URL: {url}")
        
        for scraper in self.scrapers:
            if not format in scraper.supports:
                logger.warning(f"Scraper {scraper.__class__.__name__} does not support {format} format.")
                continue
            
            logger.debug(f"Trying scraper: {scraper.__class__.__name__}")
            
            try:
                result = scraper.scrape(url, format)
            except Exception as e:
                logger.error(f"Unknown exception: {e}")
                continue
            
            logger.debug(f"Status {result.status} for {format} webpage")
            
            match result.status:
                # Not found or removed
                case status if status == 404 or (status >= 300 and status < 400):
                    logger.debug(f"URL not found or removed. Trying with archive.")
                    archive_url = self.archive.get_archive(url)
                    return self.scrape(archive_url, format)
                    
                # Forbidden
                case status if status >= 400 and status < 500:
                    logger.debug(f"URL forbidden. Trying with another scraper.")
                    continue
                
                # OK?
                case _:
                    # Check content type
                    if result.content_type not in ["text/html", "text/plain", None]:
                        logger.warning(f"Unsupported content type: {result.content_type}")
                        return False
                    
                    # Check size
                    html_size = len(result.html) if result.html else -1
                    pdf_size = len(result.pdf) if result.pdf else -1
                    
                    logger.debug(f"HTML size: {html_size if html_size != -1 else 'N/A'}")
                    logger.debug(f"PDF size: {pdf_size if pdf_size != -1 else 'N/A'}")
                    
                    if html_size > SCRAPED_SIZE_LIMIT or pdf_size > SCRAPED_SIZE_LIMIT:
                        logger.warning(f"Scraped content size exceeds limit")
                        return False
                    
                    return result
                
        return None
                
if __name__ == "__main__":
    debug.setup()
    
    # OK but javascript not enabled
    #url = "https://x.com/RadioHacking/status/1917170770868097071"
    
    #url = "https://okdiario.com/economia/sanchez-ataca-nucleares-pero-fueron-francia-que-levantaron-sistema-apagon-14686083"

    url = "https://elpais.com/espana/2025-05-14/una-explosion-provoca-un-incendio-en-una-nave-de-productos-quimicos-en-la-localidad-sevillana-de-alcala-de-guadaira.html"
    
    # Try to download an HTML
    scraper = Scraper()
    
    result = scraper.scrape(url, format=Format.HTML)
    logger.debug(f"Result: {result}")
    
    # Try to download a PDF
    result = scraper.scrape(url, format=Format.PDF)
    logger.debug(f"Result: {result}")
    
    # Try to download both HTML and PDF
    result = scraper.scrape(url, format=Format.HTML | Format.PDF)
    logger.debug(f"Result: {result}")
    if result.html:
        logger.debug(f"HTML content length: {len(result.html)}")
    if result.pdf:
        logger.debug(f"PDF content length: {len(result.pdf)}")