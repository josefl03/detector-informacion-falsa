import base64
import mimetypes
from datetime import datetime
from loguru import logger
import scipy
from urllib.parse import urlparse
import pickle
import json
from pydantic import BaseModel
import re
import dataclasses
import socket

try:
    import fake_news_detector.debug
except ImportError:
    import debug

# TEXT
def remove_newlines(text: str) -> str:
    """
    Remove newlines from the text.

    Args:
        text (str): The text to process.

    Returns:
        str: The processed text without newlines.
    """
    return text.replace("\r\n", " ").replace("\n", " ")

def short(text: str) -> str:
    """
    Summarize the text to a smaller size. Also remove newlines.
    """
    text = remove_newlines(text)
    return text[:300] + "..." if len(text) > 100 else text

def save(path: str, text: str) -> None:
    """
    Download the text to a file.

    Args:
        text (str): The text to download.
        path (str): The path to save the file.
    """
    # Create parent directories if they do not exist
    make_parents(path)
    
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)
        
        logger.debug(f"Saved to '{path}'")
        
def save_binary(path: str, b: bytes) -> None:
    """
    Download the bytes to a file.

    Args:
        b (bytes): The bytes to download.
        path (str): The path to save the file.
    """
    # Create parent directories if they do not exist
    make_parents(path)
    
    with open(path, "wb") as file:
        file.write(b)
        
        logger.debug(f"Saved to '{path}'")
        
def save_obj(path: str, obj: object) -> None:
    """
    Save an object to a file using pickle.

    Args:
        path (str): The path to save the file.
        obj (object): The object to save.
    """
    # Create parent directories if they do not exist
    make_parents(path)
    
    with open(path, "wb") as file:
        pickle.dump(obj, file)
        
        logger.debug(f"Saved object to '{path}'")

def load(path: str) -> str:
    """
    Load the text from a file.

    Args:
        path (str): The path to the file.

    Returns:
        str: The loaded text.
    """
    with open(path, "r", encoding="utf-8") as file:
        text = file.read()
        
        logger.debug(f"Loaded from '{path}'")
        
        return text
    
def load_b64(path: str, mime: str = None) -> str:
    """
    Load the bytes from a file and convert to base64.

    Args:
        path (str): The path to the file.

    Returns:
        str: The loaded bytes in base64 format.
    """
    with open(path, "rb") as file:
        b = file.read()
        
        if not mime:
            mime, _ = mimetypes.guess_type(path)
        
        logger.debug(f"Loaded '{mime}' from '{path}'")
        
        return bytes_to_b64(b, mime)

class CustomUnplickler(pickle.Unpickler):
    """
    Custom unpickler to handle unpickling errors gracefully.
    """
    def find_class(self, module, name):
        try:
            return super().find_class(module, name)
        except Exception as e:
            pass
        
        # Try appending "fake_news_detector." to the module name
        try:
            full_module_name = f"fake_news_detector.{module}"
            return super().find_class(full_module_name, name)
        except Exception as e:
            logger.error(f"Failed to find class '{name}' in module '{module}': {e}")
            return None
  
def load_obj(path: str) -> object:
    """
    Load an object from a file using pickle.

    Args:
        path (str): The path to the file.

    Returns:
        object: The loaded object.
    """
    with open(path, "rb") as file:
        obj = CustomUnplickler(file).load()
        
        logger.debug(f"Loaded object from '{path}'")
        
        return obj
    
def get_mime(content_type: str) -> str:
    """
    Get the MIME type from the content type string.

    Args:
        content_type (str): The content type string.

    Returns:
        str: The MIME type.
    """
    if not content_type:
        return None
    
    # Extract MIME type from content type
    mime = content_type.split(";")[0].strip()
    
    # If no MIME type is found, return a default
    if not mime:
        mime = None
    
    logger.debug(f"Extracted MIME type '{mime}' from content type '{content_type}'")
    
    return mime
    
## URLs
def clean_url(url: str) -> str:
    """
    Clean the URL by removing parameters.

    Args:
        url (str): The URL to clean.

    Returns:
        str: The cleaned URL.
    """
    # Remove parameters
    if "?" in url:
        url = url.split("?")[0]
    
    # Remove fragment
    if "#" in url:
        url = url.split("#")[0]
    
    return url

def get_domain(url: str) -> str:
    """
    Get the domain from the URL, removing leading 'www.' if present.

    Args:
        url (str): The URL to get the domain from.

    Returns:
        str: The domain of the URL, without leading 'www.'.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    # Remove leading 'www.' if present
    if domain.startswith('www.'):
        domain = domain[4:]
    logger.debug(f"Parsed '{url}' to '{domain}'")
    return domain

def domain_to_ip(domain: str) -> str:
    """
    Get the IP address of the domain.

    Args:
        url (str): The domain to get the IP address from.

    Returns:
        str: The IP address of the domain.
    """
    
    # Get the IP address
    ip = socket.gethostbyname(domain)
    
    logger.debug(f"Resolved '{domain}' to '{ip}'")
    
    return ip

def url_to_filepath(url: str) -> str:
    """
    Convert a URL to a permitted file path by removing the protocol and replacing unsafe characters.

    Args:
        url (str): The URL to convert.

    Returns:
        str: A safe file path string derived from the URL.
    """
    parsed = urlparse(url)
    # Remove protocol, keep netloc and path
    netloc = parsed.netloc.replace(':', '_')
    path = parsed.path.replace('/', '_')
    # Remove query and fragment
    safe = f"{netloc}{path}"
    # Optionally, add file extension if needed
    return safe

def is_valid_url(url: str) -> bool:
    """
    Check if the URL is valid.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception as e:
        logger.error(f"Invalid URL '{url}': {e}")
        return False

## HTML
def clean_html(self, html: str) -> str:
    # Remove JS, CSS, and comments
    parsed_html = self.cleaner.clean_html(html)
    
    # Remove newlines and tabs
    parsed_html = parsed_html.replace("\r\n", " ")
    parsed_html = parsed_html.replace("\n", " ")
    parsed_html = parsed_html.replace("\t", " ")
    
    return parsed_html

# DATE/TIME
def readable_datetime(dt: datetime) -> str:
    """
    Convert a datetime object to a readable string format.

    Args:
        dt (datetime): The datetime object to convert.

    Returns:
        str: Readable string representation of the datetime.
    """
    if not dt:
        return "Unknown"
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_datetime(dt: datetime, fmt: str = "%Y%m%d_%H%M%S_%f") -> str:
    """
    Format a datetime object to a string, including milliseconds.

    Args:
        dt (datetime): The datetime object to format.
        fmt (str): The format string.

    Returns:
        str: Formatted datetime string.
    """
    if not dt:
        return "Unknown"
    # %f gives microseconds; to get milliseconds, slice first 3 digits
    formatted = dt.strftime(fmt)
    if "%f" in fmt:
        ms = f"{dt.microsecond // 1000:03d}"
        formatted = formatted.replace(dt.strftime("%f"), ms)
    return formatted

# IMAGES
def image_to_b64(image_path: str) -> str:
    """
    Convert an image to base64 string.

    Args:
        image_path (str): Path to the image file.

    Returns:
        str: Base64 encoded string of the image.
    """
    mime, _ = mimetypes.guess_type(image_path)
    
    with open(image_path, "rb") as image_file:
        uri = bytes_to_b64(image_file.read(), mime)
    
        logger.debug(f"Converted '{mime}' image to base64 from '{image_path}'")
    
        return uri
    
# BYTES
def bytes_to_b64(b: bytes, mime: str) -> str:
    """
    Convert a bytes to base64 string.

    Args:
        image_path (str): Path to the image file.

    Returns:
        str: Base64 encoded string of the image.
    """
    b_b64 = base64.b64encode(b).decode('utf-8')
    uri = f"data:{mime};base64,{b_b64}"
    
    logger.debug(f"Converted '{mime}' to base64 from bytes")
    
    return uri

# LISTS
def limit(lst: list, limit: int = 10) -> list:
    """
    Limit the size of a list to a maximum number of elements.

    Args:
        lst (list): The list to limit.
        limit (int): The maximum number of elements in the list.

    Returns:
        list: The limited list.
    """
    if len(lst) > limit:
        logger.debug(f"Limiting list from {len(lst)} to {limit} elements")
        return lst[:limit]
    return lst

# EMBEDDINGS
def cosine_similarity(a: list, b: list) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        a (list): First vector.
        b (list): Second vector.

    Returns:
        float: Cosine similarity value.
    """
    return 1 - scipy.spatial.distance.cosine(a, b)

# FILES
def make_parents(path: str) -> None:
    """
    Create parent directories for the given file path if they do not exist.

    Args:
        path (str): The file path to create parents for.
    """
    import os
    
    parent_dir = os.path.dirname(path)
    
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
        
# OBJECTS
def class_to_dict(obj: object, exclude_fields: list[str] = None) -> dict:
    """
    Convert a class instance to a dictionary.

    Args:
        obj (object): The class instance to convert.
        exclude_fields (list[str], optional): List of fields to exclude from the dictionary representation.

    Returns:
        dict: Dictionary representation of the class instance.
    """
    if exclude_fields is None:
        exclude_fields = []
    data = {k: v for k, v in obj.__dict__.items() if k not in exclude_fields}
    logger.debug(f"Converted object of type '{type(obj).__name__}' to dict")
    return data

def dict_to_class(data: dict, cls: type) -> object:
    """
    Convert a dictionary to a class instance.
    
    Args:
        data (dict): The dictionary to convert.
        cls (type): The class type to convert to.
    Returns:
        object: An instance of the class with data from the dictionary.
    """
    # Ignore MongoDB ObjectId fields
    if "_id" in data:
        del data["_id"]
        
    obj = cls(**data)
    return obj

def trace_obj(obj: object) -> None:
    """
    Log all attributes and their types of an object.

    Args:
        obj (object): The object to inspect.
    """
    attrs = obj.__dict__
    for k, v in attrs.items():
        logger.debug(f"Attribute: {k}, Type: {type(v).__name__}")

def find_unpicklable_attrs(obj):
    for attr in dir(obj):
        if attr.startswith('__') or callable(getattr(obj, attr, None)):
            continue
        try:
            value = getattr(obj, attr)
            pickle.dumps(value)
        except Exception as e:
            logger.debug(f"Cannot pickle attribute: {attr} - {type(value)} - {e}")
            
def trace_basemodel(c: BaseModel):
    schema = c.model_json_schema()
    schema["additionalProperties"] = False
    
    string = str(schema)
    string = string.replace("'", '"').replace("False", "false")
    
    print(string)
    
def dataclass_to_dict(obj: object) -> dict:
    """
    Convert a dataclass instance to a dictionary.

    Args:
        obj (object): The dataclass instance to convert.

    Returns:
        dict: Dictionary representation of the dataclass.
    """
    data = dataclasses.asdict(obj)
    logger.debug(f"Converted dataclass '{type(obj).__name__}' to dict")
    return data

# INPUT
def wait_input(msg: str):
    """
    Wait for user input to continue.
    """
    input(f"{msg} (Press Enter to continue...)\n")
    
# PDF
def limit_pdf(pdf_b64: str, pages: int = 100) -> str:
    """
    Limit the number of pages in a PDF base64 string.

    Args:
        pdf_b64 (str): The base64 encoded PDF string.
        pages (int): The maximum number of pages to keep.

    Returns:
        str: The limited base64 encoded PDF string.
    """
    # This is a placeholder implementation
    # Actual implementation would require PDF manipulation libraries

if __name__ == "__main__":
    debug.setup()
    
    # Test image file to base64
    def test_image_to_b64():
        image_path = "dummy/capybara.jpg"
        b64_image = image_to_b64(image_path)
        #logger.debug(b64_image)
        assert b64_image.endswith("yNpH4pdCXombjUmeCLwvbvfcjAfhVVILYoqY00gHFIAHbqzElD9TCiJLup5M0BzouEm7XbTzEIqh6iQoRJ67wYUPWeUJr6N4U4kFMYfywOX0glQwRRAEqzef/2Q==")
    #test_image_to_b64()
    
    def test_url_to_filepath():
        url = "https://example.com/path/to/resource?query=param#fragment"
        filepath = url_to_filepath(url)
        logger.debug(f"Converted URL to filepath: {filepath}")
    #test_url_to_filepath()
    
    def test_obj_to_json():
        class TestClass:
            def __init__(self, name, value, secret):
                self.name = name
                self.value = value
                self.secret = secret
        obj = TestClass(name="Test", value=123, secret="hidden")
        data = class_to_dict(obj)
        logger.debug(f"Converted object to dict: {data}")
        # Test excluding 'secret' field
        data_exclude = class_to_dict(obj, exclude_fields=["secret"])
        logger.debug(f"Converted object to dict (exclude 'secret'): {data_exclude}")
        assert 'secret' in data
        assert 'secret' not in data_exclude
    #test_obj_to_json()
    
    def test_dict_to_class():
        class TestClass:
            def __init__(self, name, value):
                self.name = name
                self.value = value
        data = {"name": "Test", "value": 123}
        obj = dict_to_class(data, TestClass)
        logger.debug(f"Converted dict to object: {obj.name}, {obj.value}")
    #test_dict_to_class()
    
    def test_dataclass_to_dict():
        from dataclasses import dataclass
        
        @dataclass
        class TestDataClass:
            name: str
            value: int
            
        obj = TestDataClass(name="Test", value=123)
        dict_obj = dataclass_to_dict(obj)
        logger.debug(f"Converted dataclass to dict: {dict_obj}")
    #test_dataclass_to_dict()
    
    