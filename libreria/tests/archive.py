from internetarchive import search_items

def get_first_archive(url):
    """
    Fetch the first archived snapshot of a URL using the internetarchive library.
    """
    try:
        # Search for the URL in the Wayback Machine
        search_results = search_items(f'collection:web&url:{url}')
        for result in search_results:
            # Extract the first result's identifier
            identifier = result['identifier']
            return f"https://web.archive.org/web/{identifier}/{url}"
        return "No archives found for the given URL."
    except Exception as e:
        return f"Error: {e}"

# Example usage
if __name__ == "__main__":
    url = "http://example.com"
    first_archive = get_first_archive(url)
    print("First archived URL:", first_archive)