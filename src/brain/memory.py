import logging
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import time

class MemoryManager:
    """
    Manages Long-Term Vector Memory using ChromaDB.
    """
    def __init__(self, config: dict):
        self.logger = logging.getLogger("hedgemony.brain.memory")
        self.config = config.get("brain", {}).get("memory", {})
        
        self.enabled = self.config.get("enabled", True)
        if not self.enabled:
            return

        self.collection_name = self.config.get("collection_name", "market_events")
        self.persist_path = self.config.get("path", "data/chromadb")
        
        try:
            # Initialize Client
            self.client = chromadb.PersistentClient(path=self.persist_path)
            
            # Initialize Embedding Model (Local, Fast)
            # all-MiniLM-L6-v2 is standard for speed/quality balance
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Get or Create Collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"} # Cosine similarity for text
            )
            self.logger.info(f"🧠 Memory Initialized. Collection: {self.collection_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Memory: {e}")
            self.enabled = False

    def add_event(self, text: str, metadata: dict = None, event_id: str = None):
        """
        Store an event in vector memory.
        """
        if not self.enabled:
            return

        try:
            if event_id is None:
                event_id = f"evt_{int(time.time()*1000)}"
                
            if metadata is None:
                metadata = {}
                
            # Embed
            embedding = self.embedder.encode(text).tolist()
            
            # Store
            self.collection.add(
                documents=[text],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[event_id]
            )
            self.logger.debug(f"Stored event {event_id} in memory")
            
        except Exception as e:
            self.logger.error(f"Failed to add event to memory: {e}")

    def search_similar(self, text: str, n_results: int = 3):
        """
        Find historically similar events.
        """
        if not self.enabled:
            return []

        try:
            embedding = self.embedder.encode(text).tolist()
            
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results
            )
            
            # Parse ChromaDB result structure
            # results is a dict of lists: {'documents': [[...]], 'metadatas': [[...]], 'distances': [[...]]}
            parsed_results = []
            
            if results['documents']:
                for i in range(len(results['documents'][0])):
                    doc = results['documents'][0][i]
                    meta = results['metadatas'][0][i]
                    dist = results['distances'][0][i]
                    
                    parsed_results.append({
                        "text": doc,
                        "metadata": meta,
                        "distance": dist,
                        "similarity": 1 - dist # Cosine distance to similarity
                    })
            
            return parsed_results
            
        except Exception as e:
            self.logger.error(f"Memory Search Failed: {e}")
            return []
