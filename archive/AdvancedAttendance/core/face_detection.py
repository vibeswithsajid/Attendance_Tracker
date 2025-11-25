import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from loguru import logger
import threading
import pickle

class FaceDetector:
    def __init__(self, config):
        self.config = config
        self.lock = threading.Lock()
        self.models_dir = config['directories']['models']
        
        # Initialize InsightFace
        # providers: ['CUDAExecutionProvider', 'CPUExecutionProvider']
        providers = ['CPUExecutionProvider']
        if config['recognition']['device'] == 'cuda':
            providers.insert(0, 'CUDAExecutionProvider')
            
        logger.info(f"Initializing InsightFace with providers: {providers}")
        
        self.app = FaceAnalysis(
            name=config['recognition']['model_name'],
            root=self.models_dir,
            providers=providers
        )
        
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        
        # Load known faces from DB
        self.known_faces = {} # name -> embedding
        self.det_thresh = config['recognition']['det_thresh']
        self.rec_thresh = config['recognition']['rec_thresh']
        self.sim_thresh = config['recognition']['similarity_threshold']

    def load_known_faces(self, faces_list):
        """Load faces from database list into memory."""
        with self.lock:
            self.known_faces = {}
            for face in faces_list:
                try:
                    embedding = pickle.loads(face.embedding)
                    self.known_faces[face.name] = embedding
                except Exception as e:
                    logger.error(f"Error loading face {face.name}: {e}")
            logger.info(f"Loaded {len(self.known_faces)} known faces")

    def process_frame(self, frame):
        """Detect and recognize faces in a frame."""
        if frame is None:
            return []
            
        with self.lock:
            try:
                # InsightFace expects RGB
                # But sometimes it works with BGR? The docs say RGB usually.
                # Let's keep it consistent.
                # Actually, FaceAnalysis.get() usually takes BGR (OpenCV format)
                
                faces = self.app.get(frame)
                
                results = []
                for face in faces:
                    if face.det_score < self.det_thresh:
                        continue
                        
                    result = {
                        'bbox': face.bbox,
                        'kps': face.kps,
                        'det_score': face.det_score,
                        'embedding': face.embedding,
                        'age': int(face.age) if hasattr(face, 'age') else None,
                        'gender': 'M' if hasattr(face, 'gender') and face.gender == 1 else 'F',
                        'name': 'Unknown',
                        'confidence': 0.0
                    }
                    
                    # Recognition
                    if self.known_faces:
                        max_score = 0
                        best_name = "Unknown"
                        
                        for name, known_emb in self.known_faces.items():
                            # Cosine similarity
                            score = np.dot(result['embedding'], known_emb) / (
                                np.linalg.norm(result['embedding']) * np.linalg.norm(known_emb)
                            )
                            
                            if score > max_score:
                                max_score = score
                                best_name = name
                        
                        if max_score > self.sim_thresh:
                            result['name'] = best_name
                            result['confidence'] = float(max_score)
                    
                    results.append(result)
                    
                return results
                
            except Exception as e:
                logger.error(f"Face detection error: {e}")
                return []
