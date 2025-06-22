from abc import ABC, abstractmethod
from loguru import logger
from typing import List, Dict, Any
from typing import Tuple
import os

import pymongo

from fake_news_detector.datatypes import WebPage
import fake_news_detector.debug as debug
import fake_news_detector.services.llm as llm
import fake_news_detector.utils as utils

# -----------------
CHROMADB_DEFAULT_PATH = "database/chromadb"
# -----------------


class Database(ABC):
    @abstractmethod
    def __init__(self):
        pass
    
    @abstractmethod
    def clear(self):
        """
        Clear the database.
        """
        pass
    
    @abstractmethod
    def add_webpage(self, id, webpage):
        """
        Add a new document to the database.
        """
        pass
    
    @abstractmethod
    def get_webpage(self, id) -> WebPage | None:
        """
        Get a document from the database.
        """
        pass

MONGO_WEBPAGE_COLLECTION = "webpages"
MONGO_DB_NAME = "fake_news_detector"

class MongoDatabase(Database):
    def __init__(self, mongo_uri: str = os.getenv("MONGODB_BASE_URL")):
        """
        Initialize the MongoDB database connection.
        
        :param mongo_uri: MongoDB connection URI.
        """
        self.client = pymongo.MongoClient(mongo_uri)
        
        self.db = self.client[MONGO_DB_NAME]
        self.webpage_collection = self.db[MONGO_WEBPAGE_COLLECTION]
        
        logger.debug(f"Connected to MongoDB at {mongo_uri}, using database '{MONGO_DB_NAME}' and collection '{MONGO_WEBPAGE_COLLECTION}'")
        
    
    def clear(self):
        self.webpage_collection.delete_many({})
    
    def add_webpage(self, webpage: WebPage):
        logger.debug(f"Saving to cache")
        
        self.webpage_collection.insert_one(
            utils.class_to_dict(
                webpage,
                exclude_fields=["distance", "veredict"]
            )
        )
    
    def get_webpage(self, url: str) -> WebPage | None:
        data = self.webpage_collection.find_one({"url": url})
        if data:
            logger.debug(f"Found webpage in cache")
            return utils.dict_to_class(data, WebPage)
        return None
        
if __name__ == "__main__":
    debug.setup()
    
    from services.llm import OllamaEmbeddings
    
    # Initialize the embedding model
    model = OllamaEmbeddings(
        llm.LLM(
            endpoint="http://83.97.79.137:2003/v1",
            model = "all-minilm"
        )
    )
    # Embedding model
    
    # Test the database (MongoDB version)
    db = MongoDatabase(
        os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    )
    db.clear()
    
    # Create a mock webpage object
    
    # Case 1: News about sports
    text1 = "The local team won the championship after a thrilling match."
    emb1 = model.get_embeddings(text1)
    webpage1 = WebPage(
        url="http://sportsnews.com/article1",
        title="Local Team Wins Championship",
        date="2023-10-01",
        summary=text1,
        summary_embeddings=emb1,  # Fill embeddings
        distance=None,
        veredict=None
    )
    db.add_webpage(webpage1)

    # Case 2: News about technology
    text2 = "A new smartphone was released with groundbreaking features."
    emb2 = model.get_embeddings(text2)
    webpage2 = WebPage(
        url="http://techupdates.com/article2",
        title="New Smartphone Released",
        date="2023-10-02",
        summary=text2,
        summary_embeddings=emb2,  # Fill embeddings
        distance=None,
        veredict=None
    )
    db.add_webpage(webpage2)

    # Case 3: News about politics
    text3 = "The government announced new policies to improve education."
    emb3 = model.get_embeddings(text3)
    webpage3 = WebPage(
        url="http://politicsdaily.com/article3",
        title="Government Announces Education Policies",
        date="2023-10-03",
        summary=text3,
        summary_embeddings=emb3,  # Fill embeddings
        distance=None,
        veredict=None
    )
    db.add_webpage(webpage3)
    
    # Check if the document was added
    result = db.get_webpage("http://techupdates.com/article2")
    if result:
        print("Document found:", result)
    else:
        print("Document not found.")
    