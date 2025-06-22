from waybackpy import WaybackMachineCDXServerAPI
url = "https://google.com"
user_agent = "my new app's user agent"
cdx_api = WaybackMachineCDXServerAPI(url, user_agent)
print(cdx_api.oldest())