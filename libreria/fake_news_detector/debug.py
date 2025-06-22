from loguru import logger
import sys
import os
import dotenv
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime
import requests

from fake_news_detector.datatypes import *
import fake_news_detector.utils as utils

def setup(log_file: str = None):
    """
    Initialize the debug environment.    """
    # Setup loggers
    logger.remove()
    
    # Console
    logger.add(
        sys.stdout,
        level="DEBUG",
        colorize=True,
        
        backtrace=True,
        diagnose=True,
        catch=True,
        
    )
    
    # File
    log_path = log_file or "logs/{time}.log"
    logger.add(
        #"logs/latest_debug.log",
        log_path,
        level="DEBUG",
        
        backtrace=True,
        diagnose=True,
        catch=True,
    )
    
    # Remove old .log files
    logs = []
    for file in os.listdir("logs"):
        if file.endswith(".log"):
            logs.append(os.path.join("logs", file))
            
    logs.sort(key=os.path.getmtime, reverse=True)
    for log in logs[10:]:  # Keep the latest 10 logs
        os.remove(log)
    
    #logger.add("logs/tests/{time}.log", level="TRACE")

    # Load environment variables from .env file
    dotenv.load_dotenv(override=True)
    
    # Check if ollama is running
    logger.debug("Testing if LLM services are running...")
    llm_res = test_llms()
    if not llm_res:
        exit(1)
    
    logger.debug("Testing if MongoDB is running...")
    test_mongo()

def test_mongo():
    # Check if mongo is running
    mongodb_uri = os.getenv("MONGODB_BASE_URL")
    
    if mongodb_uri and "localhost" in mongodb_uri:
        try:
            client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=2000)
            
            # The following call forces a connection attempt
            client.admin.command("ping")
        
        except ConnectionFailure:
            logger.debug("Starting MongoDB server...")
            os.system("sudo systemctl start mongod")

def test_llms():
    SERVICE_ENDPOINTS = {
        "ollama": os.getenv("OLLAMA_BASE_URL"),
        "ollama-embeddings": os.getenv("OLLAMA_BASE_URL"),
        "openrouter": os.getenv("OPENROUTER_BASE_URL"),
        "openai": os.getenv("OPENAI_BASE_URL"),
    }

    services = [
        os.getenv("EMBEDDINGS_SERVICE"),
        os.getenv("PDF_SERVICE"),
        os.getenv("TEXT_SERVICE"),
    ]
    
    # Convert service to urls
    service_urls: set[str] = set()
    for service in services:
        assert service in SERVICE_ENDPOINTS, f"Service {service} is not defined in SERVICE_ENDPOINTS."
        
        url = SERVICE_ENDPOINTS.get(service)
        service_urls.add(url)
        
        #print(f"Testing service {service} at {url}")
        
    # Test all
    ok = True
    for service_url in service_urls:
        try:
            resp = requests.get(service_url)
        except requests.ConnectionError as e:
            logger.error(f"Failed to connect to LLM service: {service_url}")
            ok = False
            
    return ok
            
def save_pipe(pipe: Pipe, name: str = None):
    logger.debug(f"Saving the pipe...")
    
    now_str = utils.format_datetime(datetime.now())
    if name:
        filename = f"{now_str}_{name}.pkl"
    else:
        filename = f"{now_str}.pkl"
    
    filepath = os.path.join(os.getenv("PIPE_PATH"), filename)
    utils.save_obj(filepath, pipe)
    
def load_pipe(filename: str) -> Pipe:
    """
    Load a Pipe object from a file.
    
    Args:
        id (str): The ID of the pipe to load.
    
    Returns:
        Pipe: The loaded Pipe object.
    """
    logger.debug(f"Loading the pipe...")
    filepath = os.path.join(os.getenv("PIPE_PATH"), filename)
    return utils.load_obj(filepath)

if __name__ == "__main__":
    setup()
    logger.debug("Debug environment initialized.")
    
    # Example usage
    pipe = Pipe()  # Assuming Pipe is defined in datatypes.py
    save_pipe(pipe, "example_pipe")
    loaded_pipe = load_pipe("20250529_130515_example_pipe.pkl")
    logger.debug(f"Loaded pipe: {loaded_pipe}")