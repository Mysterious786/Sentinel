"""
Embedding service for Sentinel - Multi-provider embeddings support
Supports AWS Bedrock Titan, local sentence-transformers, and OpenAI
"""
import boto3
import json
import logging
import os
from typing import List, Dict, Any, Optional
import numpy as np
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings with multiple provider fallbacks"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.provider = self._initialize_provider()
        
    def _initialize_provider(self) -> str:
        """Initialize embedding provider with fallback logic"""
        
        # Try AWS Bedrock first (best for production)
        try:
            self.bedrock_client = boto3.client("bedrock-runtime", region_name=self.region)
            # Test connection with a simple call
            response = self.bedrock_client.list_foundation_models()
            self.model_id = "amazon.titan-embed-text-v2:0"
            logger.info("✅ AWS Bedrock embedding service initialized")
            return "bedrock"
        except (ClientError, NoCredentialsError) as e:
            logger.warning(f"AWS Bedrock not available: {e}")
        except Exception as e:
            logger.warning(f"AWS Bedrock initialization failed: {e}")
        
        # Try OpenAI as secondary option
        try:
            import openai
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                logger.info("✅ OpenAI embedding service initialized")
                return "openai"
            else:
                logger.warning("OpenAI API key not found in environment")
        except ImportError:
            logger.warning("OpenAI package not installed")
        except Exception as e:
            logger.warning(f"OpenAI initialization failed: {e}")
        
        # Fall back to local sentence transformers
        try:
            from sentence_transformers import SentenceTransformer
            self.local_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Local sentence transformer initialized")
            return "local"
        except ImportError:
            logger.warning("sentence-transformers package not installed")
        except Exception as e:
            logger.warning(f"Local model initialization failed: {e}")
        
        # Final fallback to simple TF-IDF
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.tfidf = TfidfVectorizer(max_features=1024, stop_words='english')
            self._tfidf_fitted = False
            logger.info("✅ TF-IDF fallback initialized")
            return "tfidf"
        except Exception as e:
            logger.error(f"All embedding providers failed: {e}")
            return "none"
    
    def preprocess_event(self, event_data: Dict[Any, Any]) -> str:
        """Convert event data to text for embedding"""
        # Extract key fields for semantic representation
        text_components = []
        
        # Event metadata
        if "event_type" in event_data:
            text_components.append(f"Event type: {event_data['event_type']}")
        
        if "action" in event_data:
            text_components.append(f"Action: {event_data['action']}")
        
        if "source_ip" in event_data:
            text_components.append(f"Source IP: {event_data['source_ip']}")
        
        if "username" in event_data:
            text_components.append(f"User: {event_data['username']}")
        
        if "user_agent" in event_data:
            text_components.append(f"User agent: {event_data['user_agent']}")
        
        # Geographic information
        if "geo_location" in event_data:
            geo = event_data["geo_location"]
            text_components.append(f"Location: {geo.get('country', 'unknown')} {geo.get('city', '')}")
        
        # Time patterns (hour of day, day of week)
        if "timestamp" in event_data:
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(event_data["timestamp"].replace('Z', '+00:00'))
                text_components.append(f"Hour: {dt.hour}")
                text_components.append(f"Day of week: {dt.weekday()}")
            except:
                pass
        
        # Request details for web events
        if "request" in event_data:
            req = event_data["request"]
            if "method" in req:
                text_components.append(f"HTTP method: {req['method']}")
            if "uri" in req:
                text_components.append(f"URI: {req['uri']}")
            if "status_code" in req:
                text_components.append(f"Status: {req['status_code']}")
        
        # Authentication details
        if "auth" in event_data:
            auth = event_data["auth"]
            if "success" in auth:
                text_components.append(f"Auth success: {auth['success']}")
            if "method" in auth:
                text_components.append(f"Auth method: {auth['method']}")
        
        # Join all components
        return " | ".join(text_components)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for given text using available provider"""
        
        if self.provider == "bedrock":
            return await self._bedrock_embedding(text)
        elif self.provider == "openai":
            return await self._openai_embedding(text)
        elif self.provider == "local":
            return await self._local_embedding(text)
        elif self.provider == "tfidf":
            return await self._tfidf_embedding(text)
        else:
            # Return zero vector as last resort
            logger.warning("No embedding provider available, using zero vector")
            return [0.0] * 1024
    
    async def _bedrock_embedding(self, text: str) -> List[float]:
        """Generate embedding using AWS Bedrock Titan"""
        try:
            request_body = {
                "inputText": text,
                "dimensions": 1024,
                "normalize": True
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response["body"].read())
            embedding = response_body["embedding"]
            
            logger.debug(f"Generated Bedrock embedding: {len(embedding)}D")
            return embedding
            
        except Exception as e:
            logger.error(f"Bedrock embedding error: {e}")
            return [0.0] * 1024
    
    async def _openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
                dimensions=1024
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated OpenAI embedding: {len(embedding)}D")
            return embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            return [0.0] * 1024
    
    async def _local_embedding(self, text: str) -> List[float]:
        """Generate embedding using local sentence transformer"""
        try:
            # Sentence transformers return numpy arrays
            embedding_array = self.local_model.encode([text])[0]
            
            # Pad or truncate to 1024 dimensions
            if len(embedding_array) < 1024:
                # Pad with zeros
                padded = np.zeros(1024)
                padded[:len(embedding_array)] = embedding_array
                embedding = padded.tolist()
            else:
                # Truncate to 1024
                embedding = embedding_array[:1024].tolist()
            
            logger.debug(f"Generated local embedding: {len(embedding)}D")
            return embedding
            
        except Exception as e:
            logger.error(f"Local embedding error: {e}")
            return [0.0] * 1024
    
    async def _tfidf_embedding(self, text: str) -> List[float]:
        """Generate embedding using TF-IDF (last resort fallback)"""
        try:
            if not self._tfidf_fitted:
                # For demo purposes, fit on the current text
                # In production, you'd fit on a larger corpus
                self.tfidf.fit([text])
                self._tfidf_fitted = True
            
            # Transform text to TF-IDF vector
            tfidf_vector = self.tfidf.transform([text]).toarray()[0]
            
            # Ensure 1024 dimensions
            if len(tfidf_vector) < 1024:
                padded = np.zeros(1024)
                padded[:len(tfidf_vector)] = tfidf_vector
                embedding = padded.tolist()
            else:
                embedding = tfidf_vector[:1024].tolist()
            
            logger.debug(f"Generated TF-IDF embedding: {len(embedding)}D")
            return embedding
            
        except Exception as e:
            logger.error(f"TF-IDF embedding error: {e}")
            return [0.0] * 1024
    
    async def generate_event_embedding(self, event_data: Dict[Any, Any]) -> List[float]:
        """Generate embedding for a security event"""
        text = self.preprocess_event(event_data)
        return await self.generate_embedding(text)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        
        except Exception as e:
            logger.error(f"Similarity calculation error: {e}")
            return 0.0
    
    def create_baseline_embedding(self, user_events: List[Dict[Any, Any]]) -> List[float]:
        """Create a baseline embedding representing normal user behavior"""
        if not user_events:
            return [0.0] * 1024
        
        # For now, use the average of all user event embeddings
        # In production, this would be more sophisticated
        embeddings = []
        for event in user_events:
            if "embedding" in event:
                embeddings.append(event["embedding"])
        
        if not embeddings:
            return [0.0] * 1024
        
        # Calculate mean embedding
        embeddings_array = np.array(embeddings)
        baseline = np.mean(embeddings_array, axis=0)
        
        return baseline.tolist()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current embedding provider"""
        return {
            "provider": self.provider,
            "model": getattr(self, 'model_id', 'unknown'),
            "dimensions": 1024,
            "status": "ready" if self.provider != "none" else "error"
        }


# Singleton instance
embedding_service = EmbeddingService()