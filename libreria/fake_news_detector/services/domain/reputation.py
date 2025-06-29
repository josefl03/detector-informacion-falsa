from abc import ABC, abstractmethod
from loguru import logger
import os
import asyncio
import threading
import sys
import time
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential

import vt
import requests

sys.path.append("libreria/") 
import fake_news_detector.debug as debug

class DomainReputatuion:
    @abstractmethod
    def __init__(self):
        pass
    
    @abstractmethod
    def get_reputation(self, domain: str) -> int:
        """
        Get the reputation of a domain.
        
        Args:
            domain (str): The domain to check.
        
        Returns:
            int: Reputation score.
        """
        pass
    
class VirusTotalReputation(DomainReputatuion):
    def __init__(self, api_key = None, api_url = None):
        self.api_key = os.getenv("VIRUSTOTAL_API_KEY") if api_key is None else api_key
        self.api_url = os.getenv("VIRUSTOTAL_API_URL") if api_url is None else api_url

        #assert self.api_key, "VIRUSTOTAL_API_KEY environment variable is not set"
        assert self.api_url, "VIRUSTOTAL_API_URL environment variable is not set"

        if not self.api_url.endswith("/"):
            self.api_url += "/"

        self.api_url = self.api_url

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=10, max=60*5))
    def get_reputation(self, domain: str) -> int:
        """
        Get the reputation of a domain using VirusTotal API via synchronous HTTP.
        """
        url = f"{self.api_url}{domain}"
        headers = {"x-apikey": self.api_key}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        reputation = stats.get("malicious", 0) + stats.get("suspicious", 0)
        time.sleep(1)
        return -reputation
    
if __name__ == "__main__":
    debug.setup(skip_checks=True)
    
    vtrep = VirusTotalReputation(api_key = "", api_url= "")
    domain = "example.com"
    reputation = vtrep.get_reputation(domain)
    logger.info(f"Reputation for {domain}: {reputation}")
