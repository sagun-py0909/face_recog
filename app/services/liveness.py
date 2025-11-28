import cv2
import numpy as np
from typing import List, Tuple, Optional

# Make dlib optional since it's difficult to install
try:
    import dlib
    from scipy.spatial import distance as dist
    DLIB_AVAILABLE = True
except ImportError:
    DLIB_AVAILABLE = False
    print("⚠ dlib not available - liveness detection disabled")

class LivenessDetector:
    """
    Simple liveness detection using blink detection
    For production, consider more advanced methods like depth sensing or 3D face analysis
    """
    
    def __init__(self):
        self.EYE_AR_THRESH = 0.25  # Eye aspect ratio threshold
        self.EYE_AR_CONSEC_FRAMES = 2  # Consecutive frames for blink
        self.detector = None
        self.predictor = None
        if DLIB_AVAILABLE:
            self._initialize_detector()
        else:
            print("⚠ Liveness detection disabled (dlib not installed)")
    
    def _initialize_detector(self):
        """Initialize dlib face detector and landmark predictor"""
        if not DLIB_AVAILABLE:
            return
            
        try:
            self.detector = dlib.get_frontal_face_detector()
            # Note: You'll need to download shape_predictor_68_face_landmarks.dat
            # from http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
            predictor_path = "shape_predictor_68_face_landmarks.dat"
            self.predictor = dlib.shape_predictor(predictor_path)
            print("✓ Liveness detector initialized")
        except Exception as e:
            print(f"⚠ Liveness detector not available: {e}")
            self.detector = None
            self.predictor = None
    
    def is_available(self) -> bool:
        """Check if liveness detection is available"""
        return self.detector is not None and self.predictor is not None
    
    def _eye_aspect_ratio(self, eye: np.ndarray) -> float:
        """
        Calculate eye aspect ratio (EAR)
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        """
        if not DLIB_AVAILABLE:
            return 0.0
            
        # Vertical eye landmarks
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        
        # Horizontal eye landmark
        C = dist.euclidean(eye[0], eye[3])
        
        # Eye aspect ratio
        ear = (A + B) / (2.0 * C)
        return ear
    
    def detect_blink(self, frames: List[np.ndarray]) -> Tuple[bool, str]:
        """
        Detect blink in a sequence of frames
        
        Args:
            frames: List of RGB image arrays
            
        Returns:
            Tuple of (is_live, message)
        """
        if not self.is_available():
            # Fallback: no liveness detection available
            return True, "Liveness detection not available (proceeding without check)"
        
        if len(frames) < 3:
            return False, "Insufficient frames for liveness detection (need at least 3)"
        
        blink_count = 0
        consecutive_closed = 0
        
        # Eye landmarks indices (68-point model)
        LEFT_EYE_START, LEFT_EYE_END = 42, 48
        RIGHT_EYE_START, RIGHT_EYE_END = 36, 42
        
        for frame in frames:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            # Detect faces
            faces = self.detector(gray, 0)
            
            if len(faces) == 0:
                continue
            
            # Process first face
            face = faces[0]
            shape = self.predictor(gray, face)
            
            # Convert shape to numpy array
            shape = np.array([[p.x, p.y] for p in shape.parts()])
            
            # Extract eye coordinates
            left_eye = shape[LEFT_EYE_START:LEFT_EYE_END]
            right_eye = shape[RIGHT_EYE_START:RIGHT_EYE_END]
            
            # Calculate EAR for both eyes
            left_ear = self._eye_aspect_ratio(left_eye)
            right_ear = self._eye_aspect_ratio(right_eye)
            
            # Average EAR
            ear = (left_ear + right_ear) / 2.0
            
            # Check if eyes are closed
            if ear < self.EYE_AR_THRESH:
                consecutive_closed += 1
            else:
                if consecutive_closed >= self.EYE_AR_CONSEC_FRAMES:
                    blink_count += 1
                consecutive_closed = 0
        
        if blink_count > 0:
            return True, f"Liveness confirmed (detected {blink_count} blink(s))"
        else:
            return False, "No blink detected - possible photo/video spoof"
    
    def check_motion(self, frames: List[np.ndarray]) -> Tuple[bool, str]:
        """
        Simple motion-based liveness detection
        Checks for facial movement between frames
        
        Args:
            frames: List of RGB image arrays
            
        Returns:
            Tuple of (is_live, message)
        """
        if len(frames) < 2:
            return False, "Insufficient frames for motion detection"
        
        # Convert frames to grayscale
        gray_frames = [cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in frames]
        
        # Calculate frame differences
        total_motion = 0
        for i in range(len(gray_frames) - 1):
            diff = cv2.absdiff(gray_frames[i], gray_frames[i + 1])
            motion = np.sum(diff) / (diff.shape[0] * diff.shape[1])
            total_motion += motion
        
        avg_motion = total_motion / (len(gray_frames) - 1)
        
        # Threshold for motion (adjust based on testing)
        MOTION_THRESHOLD = 5.0
        
        if avg_motion > MOTION_THRESHOLD:
            return True, f"Motion detected (score: {avg_motion:.2f})"
        else:
            return False, f"Insufficient motion (score: {avg_motion:.2f}) - possible static image"
    
    def verify_liveness(
        self, 
        frames: List[np.ndarray], 
        method: str = "motion"
    ) -> Tuple[bool, str]:
        """
        Verify liveness using specified method
        
        Args:
            frames: List of RGB image arrays
            method: "blink" or "motion"
            
        Returns:
            Tuple of (is_live, message)
        """
        if method == "blink" and self.is_available():
            return self.detect_blink(frames)
        elif method == "motion":
            return self.check_motion(frames)
        else:
            # Fallback to motion if blink detection not available
            return self.check_motion(frames)

# Singleton instance
liveness_detector = LivenessDetector()
