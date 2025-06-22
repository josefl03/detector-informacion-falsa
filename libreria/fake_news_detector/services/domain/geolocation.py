from abc import ABC, abstractmethod
import requests
from loguru import logger
from typing import Union

import fake_news_detector.datatypes as datatypes

class DomainGeolocation(ABC):
    """
    Domain Geolocation class to represent geolocation data.
    """

    @abstractmethod
    def __init__(self, ):
        pass
    
    @abstractmethod
    def locate(self, ip: str) -> Union[str, str]:
        """
        Locate the domain and return geolocation data.
        
        Args:
            domain (str): The domain to locate.
        
        Returns:
            dict: Geolocation data.
        """
        pass
    
class IpInfoGeolocation(DomainGeolocation):

    def __init__(self):
        pass
    
    def locate(self, ip: str) -> Union[str, str]:
        resp = requests.get(f"https://ipinfo.io/{ip}/json")
        
        if resp.status_code != 200:
            logger.error(f"Failed to get geolocation data for '{ip}': {resp.status_code}")
            return None
        
        data = resp.json()
        return data["country"], data["region"]
    
if __name__ == "__main__":
    geo = IpInfoGeolocation()
    ip = "23.192.228.80"
    data = geo.locate(ip)
    print(data)