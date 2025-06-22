import requests
from abc import ABC, abstractmethod
from loguru import logger
from playwright.sync_api import sync_playwright
import playwright
from typing import Union
from bs4 import BeautifulSoup
from dataclasses import dataclass
from enum import Flag, auto

import fake_news_detector.debug as debug
import fake_news_detector.network as network
import fake_news_detector.utils as utils

# 400-500 forbidden

class Format(Flag):
    HTML = auto()
    PDF = auto()
    
@dataclass
class ScrapeResult:
    status: int
    title: str
    
    content_type: str = None
    
    html: str = None
    pdf: str = None # in base64 format
        
class Scraper(ABC):
    supports: Format
    
    def __init__(self, supports: Format):
        self.supports = supports
    
    @abstractmethod
    def scrape(self, url: str, format: Format) -> ScrapeResult:
        """
        Scrape the given URL and return the result.
        
        Args:
            url (str): The URL to scrape.
            format (Format): The format to scrape (HTML, PDF, or both).
        Returns:
            ScrapeResult: The result of the scraping, containing status, title, HTML, and PDF.
        """

class RequestsScraper(Scraper):
    def __init__(self):
        super().__init__(supports=Format.HTML)
        
    def scrape(self, url: str, format: Format) -> ScrapeResult:
        # HTML-Only
        if Format.PDF in format:
            raise NotImplementedError("PDF scraping is not implemented in RequestsScraper.")
        
        url_filepath = utils.url_to_filepath(url)
        
        res = requests.get(url=url, headers={
            "User-Agent": network.get_useragent(),
        }, timeout=10)
        
        status = res.status_code
        html = res.text
        content_type = utils.get_mime(res.headers.get("Content-Type"))
        
        soup = BeautifulSoup(html, "html.parser")
        if soup.title:
            title = soup.title.string
        else:
            title = url
                
        # Log the resulting HTML
        utils.save(f"logs/files/{url_filepath}", html)
        
        return ScrapeResult(
            status=status,
            title=title,
            html=html,
            content_type=content_type,
        )

PLAYWRIGHT_WAIT = 3000
PLAYWRIGHT_EXTENSIONS = "database/chrome/ublock-origin,database/chrome/i-dont-care-about-cookies"

class PlaywrightScraper(Scraper):
    def __init__(self):
        super().__init__(supports=Format.HTML | Format.PDF)
        
    def launch_browser(self, playwright, url: str) -> Union[int, "playwright.Page", str, str]:
        # browser = playwright.chromium.launch_persistent_context(
        #     user_data_dir="database/chrome/user-data",
        #     headless=False,
        #     args=[
        #         #"--headless=new",
        #         f"--disable-extensions-except={PLAYWRIGHT_EXTENSIONS}",
        #         f"--load-extension={PLAYWRIGHT_EXTENSIONS}",
        #         "--no-startup-window",
        #     ]
        # )
        
        browser = playwright.chromium.launch(
            headless=True,
        )
        
        # For launch_persistent_context, browser is actually a context
        context = browser
        page = context.new_page()
        
        response = page.goto(url, timeout=11000)
        page.wait_for_timeout(PLAYWRIGHT_WAIT) # TODO: wait for the page to fully load
        
        status = response.status
        title = page.title() or  url
        content_type = utils.get_mime(response.headers.get("content-type"))
        
        return status, page, title, content_type
    
    def scrape(self, url: str, format: Format) -> ScrapeResult:
        url_filepath = utils.url_to_filepath(url)
        
        with sync_playwright() as p:
            status, page, title, content_type = self.launch_browser(p, url)
            
            html = None
            if Format.HTML in format:
                html = page.content()
                
                # Log the resulting HTML
                utils.save(f"logs/files/{url_filepath}", html)
            
            pdf_b64 = None
            if Format.PDF in format:
                pdf = page.pdf(
                    print_background=True, # to include images
                    #format="A4",
                )
                pdf_b64 = utils.bytes_to_b64(pdf, "application/pdf")
                
                # Log the resulting PDF
                utils.save_binary(f"logs/files/{url_filepath}.pdf", pdf)
        
            return ScrapeResult(
                status=status,
                title=title,
                html=html,
                pdf=pdf_b64,
                content_type=content_type,
            )
        
if __name__ == "__main__":
    debug.setup()
    
    # 200
    #url = "https://www.bbc.com/news/articles/c77nm44g081o"
    #url = "https://elpais.com/economia/2025-04-29/ultima-hora-del-apagon-en-directo.html"
    
    # 403 forbidden
    #url = "https://okdiario.com/economia/sanchez-ataca-nucleares-pero-fueron-francia-que-levantaron-sistema-apagon-14686083"
    
    # Blocked to only JS
    #url = "https://x.com/RadioHacking/status/1917170770868097071"
    
    url = "https://elpais.com/espana/2025-05-14/una-explosion-provoca-un-incendio-en-una-nave-de-productos-quimicos-en-la-localidad-sevillana-de-alcala-de-guadaira.html"
    
    # Test RequestsScraper
    requests_scraper = PlaywrightScraper()
    def test_requests_scraper():
        logger.debug(f"Testing RequestsScraper with URL: {url}")
        result = requests_scraper.scrape(url, Format.HTML)
        logger.debug(f"Status: {result.status}, Title: {result.title}")
    #test_requests_scraper()
    
    # Test RequestsScraper with PDF
    def test_requests_scraper_pdf():
        logger.debug(f"Testing RequestsScraper with PDF format for URL: {url}")
        try:
            result = requests_scraper.scrape(url, Format.PDF)
            logger.debug(f"Status: {result.status}, Title: {result.title}")
        except NotImplementedError as e:
            logger.error(f"Error: {e}")
    #test_requests_scraper_pdf()
    
    # Test PlaywrightScraper
    playwright_scraper = PlaywrightScraper()
    def test_playwright_scraper():
        logger.debug(f"Testing PlaywrightScraper with URL: {url}")
        result = playwright_scraper.scrape(url, Format.HTML)
        logger.debug(f"Status: {result.status}, Title: {result.title}")
    #test_playwright_scraper()
    
    # Test PlaywrightScraper with PDF
    #def test_playwright_scraper_pdf():
        logger.debug(f"Testing PlaywrightScraper with PDF format for URL: {url}")
        result = playwright_scraper.scrape(url, Format.PDF)
        logger.debug(f"Status: {result.status}, Title: {result.title}")
    #test_playwright_scraper_pdf()
    
    # Test PlaywrightScraper with both HTML and PDF
    def test_playwright_scraper_both():
        logger.debug(f"Testing PlaywrightScraper with both HTML and PDF formats for URL: {url}")
        result = playwright_scraper.scrape(url, Format.HTML | Format.PDF)
        logger.debug(f"Status: {result.status}, Title: {result.title}")
        if result.html:
            logger.debug(f"HTML content length: {len(result.html)}")
        if result.pdf:
            logger.debug(f"PDF content length: {len(result.pdf)}")
    #test_playwright_scraper_both()
    
    def test_content_type():
        logger.debug(f"Testing content type for URL: {url}")
        try:
            result = requests_scraper.scrape(url, Format.HTML)
            print(f"Content type: {result.content_type}")
        except Exception as e:
            logger.error(f"Error fetching content type: {e}")
    #test_content_type()