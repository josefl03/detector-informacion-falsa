import random
from fake_useragent import UserAgent

def get_useragent() -> str:
    """
    Get a random user agent string.
    """
    ua = UserAgent()
    return ua.random

# Test
if __name__ == "__main__":
    # useragent
    def test_useragent():
        user_agent = get_useragent()
        print(user_agent)
    test_useragent()