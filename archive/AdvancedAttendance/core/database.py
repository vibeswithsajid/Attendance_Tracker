from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, LargeBinary, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class FaceLog(Base):
    __tablename__ = 'face_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    camera_id = Column(String(50))
    camera_name = Column(String(100))
    face_name = Column(String(100))
    age = Column(Integer)
    gender = Column(String(10))
    confidence = Column(Float)
    screenshot_path = Column(String(255))

class KnownFace(Base):
    __tablename__ = 'known_faces'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    embedding = Column(LargeBinary, nullable=False)  # Store numpy array as bytes
    image_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)

class AttendanceSession(Base):
    __tablename__ = 'attendance_sessions'
    
    id = Column(Integer, primary_key=True)
    person_name = Column(String(100), nullable=False)
    camera_id = Column(String(50))
    camera_name = Column(String(100))
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime)
    total_seconds = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)

class FaceDatabase:
    def __init__(self, db_path="data/database.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.Session()

    def add_log(self, log_data):
        session = self.Session()
        try:
            log = FaceLog(**log_data)
            session.add(log)
            session.commit()
            return log.id
        except Exception as e:
            session.rollback()
            print(f"DB Error: {e}")
        finally:
            session.close()

    def get_known_faces(self):
        session = self.Session()
        try:
            return session.query(KnownFace).all()
        finally:
            session.close()

    def add_known_face(self, name, embedding, image_path):
        session = self.Session()
        try:
            face = KnownFace(
                name=name,
                embedding=embedding,
                image_path=image_path
            )
            session.add(face)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"DB Error: {e}")
            return False
        finally:
            session.close()
