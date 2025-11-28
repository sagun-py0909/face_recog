import os
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple
from keras_facenet import FaceNet
from app.core.config import get_settings

settings = get_settings()

# Initialize models
class FaceRecognitionService:
    def __init__(self):
        self.detector = None
        self.embedder = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize face detection and embedding models"""
        # Try models/ directory first, then root
        base_dir = Path(__file__).parent.parent.parent
        proto_path = base_dir / "models" / settings.proto_path
        model_path = base_dir / "models" / settings.model_path
        
        # Fallback to root directory
        if not proto_path.exists():
            proto_path = base_dir / settings.proto_path
        if not model_path.exists():
            model_path = base_dir / settings.model_path
        
        self.detector = cv2.dnn.readNetFromCaffe(str(proto_path), str(model_path))
        self.embedder = FaceNet()
    
    def detect_and_crop(self, img: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect face in image and return cropped face region
        
        Args:
            img: RGB image array
            
        Returns:
            Cropped face image (160x160) or None if no face detected
        """
        h, w = img.shape[:2]
        blob = cv2.dnn.blobFromImage(
            cv2.resize(img, (300, 300)),
            1.0, (300, 300),
            (104.0, 177.0, 123.0)
        )
        
        self.detector.setInput(blob)
        detections = self.detector.forward()
        
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > settings.confidence_threshold:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                x1, y1, x2, y2 = box.astype(int)
                
                # Add padding and boundary checks
                padding = 10
                x1 = max(0, x1 - padding)
                y1 = max(0, y1 - padding)
                x2 = min(w, x2 + padding)
                y2 = min(h, y2 + padding)
                
                face = img[y1:y2, x1:x2]
                
                if face.size > 0 and face.shape[0] > 0 and face.shape[1] > 0:
                    return cv2.resize(face, (160, 160))
        
        return None
    
    def get_embedding(self, face: np.ndarray) -> np.ndarray:
        """
        Generate face embedding vector
        
        Args:
            face: Cropped face image (160x160)
            
        Returns:
            Face embedding vector
        """
        return self.embedder.embeddings([face])[0]
    
    def process_image(self, img: np.ndarray) -> Optional[np.ndarray]:
        """
        Process image and return face embedding
        
        Args:
            img: RGB image array
            
        Returns:
            Face embedding or None if no face detected
        """
        face = self.detect_and_crop(img)
        if face is None:
            return None
        return self.get_embedding(face)
    
    def calculate_similarity(
        self, 
        embedding1: np.ndarray, 
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First face embedding
            embedding2: Second face embedding
            
        Returns:
            Similarity score (0-1)
        """
        from sklearn.metrics.pairwise import cosine_similarity
        return float(cosine_similarity([embedding1], [embedding2])[0][0])
    
    def find_best_match(
        self,
        query_embedding: np.ndarray,
        database_embeddings: List[np.ndarray],
        threshold: float = None
    ) -> Tuple[Optional[int], Optional[float]]:
        """
        Find best matching face from database
        
        Args:
            query_embedding: Query face embedding
            database_embeddings: List of database face embeddings
            threshold: Similarity threshold (uses config default if None)
            
        Returns:
            Tuple of (index, similarity_score) or (None, None) if no match
        """
        if not database_embeddings:
            return None, None
        
        if threshold is None:
            threshold = settings.similarity_threshold
        
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity([query_embedding], database_embeddings)[0]
        
        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])
        
        if best_score >= threshold:
            return best_idx, best_score
        
        return None, best_score

# Singleton instance
face_service = FaceRecognitionService()
