from abc import ABC, abstractmethod
from loguru import logger
from typing import List, Dict, Any
from typing import Tuple
import os
import numpy as np

import faiss

from fake_news_detector.datatypes import EmbeddingsResult
import fake_news_detector.debug as debug
import fake_news_detector.services.llm as llm
import fake_news_detector.utils as utils

class EmbeddingsDatabase(ABC):
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
    def add(self, url: str, embeddings: list[float]) -> None:
        """
        Save embeddings to the database.
        
        Args:
            url (str): The URL of the webpage.
            embeddings (list[float]): The embeddings to save.
        """
        pass
    
    @abstractmethod
    def query(self, embeddings: list[float]) -> list[EmbeddingsResult]:
        """
        Query the database for similar embeddings.
        
        Args:
            embeddings (list[float]): The embeddings to query against.
        
        Returns:
            list[EmbeddingsResult]: A list of results containing URLs and distances.
        """
        pass

OLLAMA_ALLMINILM_EMBEDDING_SIZE = 384

class FaissEmbeddingsDatabase(EmbeddingsDatabase):
    id_dict: Dict[int, str] = {}
    
    def __init__(self):
        basic_index = faiss.IndexFlatL2(OLLAMA_ALLMINILM_EMBEDDING_SIZE)
        self.index = faiss.IndexIDMap(basic_index)
        
    def count(self) -> int:
        """
        Get the number of embeddings in the database.
        
        Returns:
            int: The number of embeddings.
        """
        return self.index.ntotal
    
    def clear(self):
        """
        Clear the database.
        """
        logger.debug("Clearing the embeddings database.")
        self.index.reset()
        
    def add(self, url: str, embeddings: list[float]) -> None:
        """
        Save embeddings to the database.
        
        Args:
            url (str): The URL of the webpage.
            embeddings (list[float]): The embeddings to save.
        """
        if not isinstance(embeddings, list) or not all(isinstance(x, float) for x in embeddings):
            raise ValueError("Embeddings must be a list of floats.")
        
        if len(embeddings) != OLLAMA_ALLMINILM_EMBEDDING_SIZE:
            raise ValueError(f"Embeddings must have exactly {OLLAMA_ALLMINILM_EMBEDDING_SIZE} dimensions. Received {len(embeddings)} dimensions.")
        
        
        id = self.count()
        
        
        # Update the ID dictionary
        self.id_dict[id] = url
        
        # Write the embeddings to the index
        self.index.add_with_ids(
            np.array([embeddings], dtype='float32'),  # Ensure 2D array
            np.array([id], dtype='int64')
        )
        
        logger.debug(f"Saved embeddings for ID {id}")
        
    def query(self, embeddings: list[float], max: int = 10) -> List[EmbeddingsResult]:
        """
        Query the database for similar embeddings.
        
        Args:
            embeddings (list[float]): The embeddings to query against.
        
        Returns:
            list[EmbeddingsResult]: A list of results containing URLs and distances.
        """
        if not isinstance(embeddings, list) or not all(isinstance(x, float) for x in embeddings):
            raise ValueError("Embeddings must be a list of floats.")
        
        if len(embeddings) != OLLAMA_ALLMINILM_EMBEDDING_SIZE:
            raise ValueError(f"Embeddings must have exactly {OLLAMA_ALLMINILM_EMBEDDING_SIZE} dimensions.")
        
        # Convert to numpy array
        query_vector = np.array([embeddings], dtype='float32')
        
        # Search the index
        distances, indices = self.index.search(query_vector, max)
        results = []
        
        for i, distance in zip(indices[0], distances[0]):
            if i == -1:
                # No more results
                break
            
            if not self.id_dict.get(i):
                logger.error(f"ID {i} not found in id_dict. Skipping...")
                continue
            
            results.append(
                EmbeddingsResult(
                    url=self.id_dict[i],
                    distance=distance
                )
            )
            
        return results
    
if __name__ == "__main__":
    debug.setup()
    
    
    
    # Initialize the embedding model
    model = llm.OllamaEmbeddings()
    
    # Initialize the embeddings database
    db = FaissEmbeddingsDatabase()
    db.clear()
    logger.info("Embeddings database initialized and cleared.")
    logger.info(f"Embeddings database count: {db.count()}")
    
    # Example usage
    url = "https://example.com/news-article"
    text = "The government has announced new policies to improve the economy."
    embeddings = model.get_embeddings(text)
    db.add(url, embeddings)
    
    url = "https://example.com/tech-article"
    text = "This new smartphone has groundbreaking features that will change the market."
    embeddings = model.get_embeddings(text)
    db.add(url, embeddings)
    logger.info(f"Embeddings database count after writing: {db.count()}")
    logger.info("Embeddings saved to the database.")
    
    # Query the database
    query_text = "Smartphone"
    query_embeddings = model.get_embeddings(query_text)
    results = db.query(query_embeddings, max=4)
    logger.info(f"Query results: {len(results)} found.")
    for result in results:
        logger.info(f"URL: {result.url}, Distance: {result.distance}")
        logger.info(f"Embeddings database count: {db.count()}")

