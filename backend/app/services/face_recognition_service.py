"""
Face Recognition Service using MTCNN + FaceNet for selfie verification.
Compares selfie with government ID photo to ensure the same person.
"""

import numpy as np
import io
import base64
from typing import Optional, Dict, Tuple
import logging
from PIL import Image, ImageEnhance
import httpx

logger = logging.getLogger(__name__)

try:
    import cv2
    from mtcnn import MTCNN
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    logger.warning("Face recognition libraries not installed. Install: pip install mtcnn face_recognition opencv-python")


class FaceRecognitionService:
    """Handles biometric face matching between selfie and govt ID photo."""
    
    FACE_MATCH_THRESHOLD = 0.65  # Cosine similarity threshold (0.0 to 1.0)
    IMAGE_SIZE = (224, 224)
    
    def __init__(self):
        self.detector = None
        if FACE_RECOGNITION_AVAILABLE:
            try:
                self.detector = MTCNN()
                logger.info("MTCNN detector initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize MTCNN: {e}")
    
    @staticmethod
    def _download_image(image_url: str) -> Optional[Image.Image]:
        """Download image from URL (Firestore storage or similar)."""
        try:
            with httpx.Client() as client:
                response = client.get(image_url, timeout=10.0)
                response.raise_for_status()
                return Image.open(io.BytesIO(response.content)).convert('RGB')
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            return None
    
    @staticmethod
    def _decode_base64_image(image_data: str) -> Optional[Image.Image]:
        """Decode base64 image string to PIL Image."""
        try:
            # Remove data URI prefix if present
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            return Image.open(io.BytesIO(image_bytes)).convert('RGB')
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
            return None
    
    @staticmethod
    def _enhance_contrast(image: Image.Image) -> Image.Image:
        """Apply CLAHE-like contrast enhancement."""
        try:
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(1.5)  # Increase contrast by 50%
        except Exception as e:
            logger.warning(f"Contrast enhancement failed: {e}")
            return image
    
    def _extract_face_embedding(self, image: Image.Image) -> Optional[np.ndarray]:
        """
        Extract face embedding using face_recognition (ResNet backbone).
        Returns 128-dimensional face encoding vector.
        """
        try:
            if not FACE_RECOGNITION_AVAILABLE:
                logger.error("Face recognition libraries not available")
                return None
            
            # Convert PIL Image to numpy array
            image_array = np.array(image)
            
            # Detect faces
            face_locations = face_recognition.face_locations(image_array)
            
            if not face_locations:
                logger.warning("No face detected in image")
                return None
            
            # Extract embedding from first detected face
            face_encodings = face_recognition.face_encodings(
                image_array, 
                face_locations,
                model='small'  # Use small model for speed
            )
            
            if not face_encodings:
                logger.warning("Could not extract face encoding")
                return None
            
            return face_encodings[0]  # Return first face embedding
        
        except Exception as e:
            logger.error(f"Face embedding extraction failed: {e}")
            return None
    
    def _compute_face_distance(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two face embeddings (0 = different, 1 = identical).
        Uses L2-normalized vectors for cosine distance.
        """
        try:
            # Normalize embeddings
            embedding1_norm = embedding1 / np.linalg.norm(embedding1)
            embedding2_norm = embedding2 / np.linalg.norm(embedding2)
            
            # Compute cosine similarity
            cosine_similarity = np.dot(embedding1_norm, embedding2_norm)
            
            # Convert to distance (higher score = more similar)
            return float(np.clip(cosine_similarity, 0.0, 1.0))
        
        except Exception as e:
            logger.error(f"Face distance computation failed: {e}")
            return 0.0
    
    def verify_selfie_with_id(
        self,
        selfie_image_data: str,  # Base64 or URL
        id_image_url: str,  # Firestore storage URL
        is_selfie_base64: bool = True
    ) -> Dict[str, any]:
        """
        Verify that selfie matches government ID photo.
        
        Args:
            selfie_image_data: Base64-encoded selfie or selfie URL
            id_image_url: URL to government ID image
            is_selfie_base64: Whether selfie_image_data is base64 (True) or URL (False)
        
        Returns:
            {
                "verified": bool,
                "match_score": float,  # 0.0-1.0, cosine similarity
                "confidence": float,   # 0-100%
                "error": Optional[str]
            }
        """
        try:
            # Load selfie
            selfie_image = (
                self._decode_base64_image(selfie_image_data) 
                if is_selfie_base64 
                else self._download_image(selfie_image_data)
            )
            
            if selfie_image is None:
                return {
                    "verified": False,
                    "match_score": 0.0,
                    "confidence": 0.0,
                    "error": "Failed to load selfie image"
                }
            
            # Load government ID image
            id_image = self._download_image(id_image_url)
            if id_image is None:
                return {
                    "verified": False,
                    "match_score": 0.0,
                    "confidence": 0.0,
                    "error": "Failed to load government ID image"
                }
            
            # Enhance both images for better detection
            selfie_enhanced = self._enhance_contrast(selfie_image)
            id_enhanced = self._enhance_contrast(id_image)
            
            # Extract embeddings
            selfie_embedding = self._extract_face_embedding(selfie_enhanced)
            id_embedding = self._extract_face_embedding(id_enhanced)
            
            if selfie_embedding is None or id_embedding is None:
                return {
                    "verified": False,
                    "match_score": 0.0,
                    "confidence": 0.0,
                    "error": "Could not detect face in one or both images"
                }
            
            # Compute face distance (0 = different, 1 = identical)
            match_score = self._compute_face_distance(selfie_embedding, id_embedding)
            
            # Determine verification result
            verified = match_score >= self.FACE_MATCH_THRESHOLD
            confidence = match_score * 100
            
            logger.info(
                f"Face verification: score={match_score:.4f}, "
                f"threshold={self.FACE_MATCH_THRESHOLD}, verified={verified}"
            )
            
            return {
                "verified": verified,
                "match_score": match_score,
                "confidence": confidence,
                "error": None
            }
        
        except Exception as e:
            logger.error(f"Face verification failed: {e}", exc_info=True)
            return {
                "verified": False,
                "match_score": 0.0,
                "confidence": 0.0,
                "error": f"Face verification error: {str(e)}"
            }
    
    def extract_face_embedding_from_image(
        self,
        image_data: str,
        is_base64: bool = True
    ) -> Optional[str]:
        """
        Extract face embedding from image and return as JSON string.
        Used for storing in database for later comparisons.
        """
        try:
            image = (
                self._decode_base64_image(image_data)
                if is_base64
                else self._download_image(image_data)
            )
            
            if image is None:
                logger.error("Could not load image for embedding extraction")
                return None
            
            enhanced_image = self._enhance_contrast(image)
            embedding = self._extract_face_embedding(enhanced_image)
            
            if embedding is None:
                logger.error("Could not extract face embedding")
                return None
            
            # Convert numpy array to JSON string
            return base64.b64encode(embedding.tobytes()).decode()
        
        except Exception as e:
            logger.error(f"Failed to extract face embedding: {e}")
            return None
