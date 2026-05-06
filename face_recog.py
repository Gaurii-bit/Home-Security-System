"""
Face Detection and Recognition Module
Implements face detection, feature extraction, and identity recognition
"""

import cv2
import numpy as np
from deepface import DeepFace
from typing import List, Tuple, Optional, Dict
import os

class FaceRecognitionEngine:
    """Handles face detection, preprocessing, and recognition"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        """
        Initialize face recognition engine
        
        Args:
            similarity_threshold: Threshold for face matching (0-1)
        """
        self.similarity_threshold = similarity_threshold
        self.known_embeddings = {}  # {user_id: [embeddings]}
        
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in a frame using DeepFace
        
        Args:
            frame: Input image (BGR format from OpenCV)
            
        Returns:
            List of face locations as (top, right, bottom, left)
        """
        try:
            # DeepFace.extract_faces expects BGR array and converts it internally
            # Using opencv backend for speed
            face_objs = DeepFace.extract_faces(
                img_path=frame, 
                detector_backend='opencv', 
                enforce_detection=True,
                align=False
            )
            
            locations = []
            for face_obj in face_objs:
                area = face_obj['facial_area']
                # Convert to (top, right, bottom, left) format
                top = area['y']
                right = area['x'] + area['w']
                bottom = area['y'] + area['h']
                left = area['x']
                locations.append((top, right, bottom, left))
                
            return locations
        except ValueError:
            # ValueError is raised when no faces are found
            return []
        except Exception as e:
            print(f"[ERROR] Face detection failed: {e}")
            return []
    
    def extract_face_region(self, frame: np.ndarray, location: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Extract and crop face region from frame
        
        Args:
            frame: Input image
            location: Face location (top, right, bottom, left)
            
        Returns:
            Cropped face image
        """
        top, right, bottom, left = location
        face_image = frame[top:bottom, left:right]
        return face_image
    
    def preprocess_face(self, face_image: np.ndarray, target_size: Tuple[int, int] = (128, 128)) -> np.ndarray:
        """
        Normalize and preprocess face image
        
        Args:
            face_image: Face image
            target_size: Target size for normalization
            
        Returns:
            Preprocessed face image
        """
        # Resize to standard size
        normalized = cv2.resize(face_image, target_size)
        
        # Convert to grayscale for histogram equalization
        gray = cv2.cvtColor(normalized, cv2.COLOR_BGR2GRAY)
        
        # Apply histogram equalization for better lighting normalization
        equalized = cv2.equalizeHist(gray)
        
        # Convert back to BGR
        normalized = cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR)
        
        return normalized
    
    def extract_features(self, frame: np.ndarray, face_location: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        Extract feature embedding from face using DeepFace (Facenet)
        
        Args:
            frame: Input image
            face_location: Face location (top, right, bottom, left)
            
        Returns:
            128-dimensional embedding vector
        """
        top, right, bottom, left = face_location
        # Add a small margin to ensure face is fully captured for the model
        h, w = frame.shape[:2]
        margin_y = int((bottom - top) * 0.1)
        margin_x = int((right - left) * 0.1)
        
        # Safe crop with margins
        crop_top = max(0, top - margin_y)
        crop_bottom = min(h, bottom + margin_y)
        crop_left = max(0, left - margin_x)
        crop_right = min(w, right + margin_x)
        
        face_img = frame[crop_top:crop_bottom, crop_left:crop_right]
        
        if face_img.size == 0:
            return None
            
        try:
            # We use Facenet which gives a 128-dimensional embedding, matching our DB structure
            # We skip detection here because we already cropped the face
            objs = DeepFace.represent(
                img_path=face_img, 
                model_name="Facenet", 
                detector_backend="skip", 
                enforce_detection=False
            )
            
            if len(objs) > 0:
                embedding = objs[0]['embedding']
                return np.array(embedding, dtype=np.float32)
            
            return None
        except Exception as e:
            print(f"[ERROR] Feature extraction failed: {e}")
            return None
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1)
        """
        # Cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Convert to 0-1 range (cosine similarity is -1 to 1)
        similarity = (similarity + 1) / 2
        
        return similarity
    
    def load_embeddings(self, embeddings_dict: Dict[str, List[np.ndarray]]):
        """
        Load known embeddings from database
        
        Args:
            embeddings_dict: Dictionary of {user_id: [embedding_vectors]}
        """
        self.known_embeddings = embeddings_dict
        print(f"[OK] Loaded {len(self.known_embeddings)} user embeddings")
    
    def add_embedding(self, user_id: str, embedding: np.ndarray):
        """
        Add a new embedding for a user
        
        Args:
            user_id: User identifier
            embedding: Face embedding vector
        """
        if user_id not in self.known_embeddings:
            self.known_embeddings[user_id] = []
        self.known_embeddings[user_id].append(embedding)
    
    def recognize_face(self, embedding: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Recognize face by comparing with stored embeddings
        
        Args:
            embedding: Face embedding to identify
            
        Returns:
            Tuple of (user_id, similarity_score) or (None, 0.0) if unknown
        """
        best_match_id = None
        best_similarity = 0.0
        
        for user_id, user_embeddings in self.known_embeddings.items():
            for stored_embedding in user_embeddings:
                similarity = self.compute_similarity(embedding, stored_embedding)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_id = user_id
        
        # Check if similarity exceeds threshold
        if best_similarity >= self.similarity_threshold:
            return best_match_id, best_similarity
        else:
            return None, best_similarity
    
    def process_frame(self, frame: np.ndarray) -> List[Dict]:
        """
        Complete pipeline: detect, extract, and recognize faces in frame
        
        Args:
            frame: Input frame
            
        Returns:
            List of detection results with locations and identities
        """
        results = []
        
        # Detect faces
        face_locations = self.detect_faces(frame)
        
        for location in face_locations:
            # Extract features
            embedding = self.extract_features(frame, location)
            
            if embedding is not None:
                # Recognize
                user_id, similarity = self.recognize_face(embedding)
                
                # Preprocess face for visualization
                face_image = self.extract_face_region(frame, location)
                normalized_face = self.preprocess_face(face_image)
                
                result = {
                    'location': location,
                    'embedding': embedding,
                    'user_id': user_id,
                    'similarity': similarity,
                    'face_image': normalized_face,
                    'is_authorized': user_id is not None
                }
                
                results.append(result)
        
        return results
    
    def draw_results(self, frame: np.ndarray, results: List[Dict]) -> np.ndarray:
        """
        Draw bounding boxes and labels on frame
        
        Args:
            frame: Input frame
            results: Detection results from process_frame()
            
        Returns:
            Annotated frame
        """
        output_frame = frame.copy()
        
        for result in results:
            top, right, bottom, left = result['location']
            user_id = result['user_id']
            similarity = result['similarity']
            is_authorized = result['is_authorized']
            
            # Choose color based on authorization
            if is_authorized:
                color = (0, 255, 0)  # Green for authorized
                name = result.get('name', user_id)
                role = result.get('role', '')
                label = f"{name} | {role} ({similarity:.2f})"
            else:
                color = (0, 0, 255)  # Red for unknown
                label = f"Unknown ({similarity:.2f})"
            
            # Draw rectangle
            cv2.rectangle(output_frame, (left, top), (right, bottom), color, 2)
            
            # Draw label background
            cv2.rectangle(output_frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            
            # Draw label text
            cv2.putText(output_frame, label, (left + 6, bottom - 6),
                       cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        
        return output_frame