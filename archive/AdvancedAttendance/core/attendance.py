import time
from datetime import datetime
from loguru import logger
import threading

class AttendanceTracker:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.active_sessions = {} # name -> {start_time, last_seen, camera_id, db_id}
        self.lock = threading.Lock()
        self.timeout = config['attendance']['session_timeout']
        self.cooldown = config['attendance']['cooldown']
        self.last_processed = {} # name -> timestamp

    def process_detection(self, detection, camera_id, camera_name):
        name = detection['name']
        if name == "Unknown":
            return

        now = time.time()
        
        # Rate limiting for processing
        if name in self.last_processed:
            if now - self.last_processed[name] < self.cooldown:
                return
        self.last_processed[name] = now

        with self.lock:
            if name in self.active_sessions:
                # Update existing session
                self.active_sessions[name]['last_seen'] = now
                self.active_sessions[name]['camera_id'] = camera_id
            else:
                # Start new session
                logger.info(f"New session started for {name} on {camera_name}")
                
                # Create DB entry
                session_data = {
                    'person_name': name,
                    'camera_id': camera_id,
                    'camera_name': camera_name,
                    'entry_time': datetime.now(),
                    'is_active': True
                }
                
                # We need a method in DB to create session and return ID
                # For now, let's assume we handle the DB object directly or add a method
                # Let's use the DB object passed in
                session = self.db.get_session()
                try:
                    from core.database import AttendanceSession
                    new_session = AttendanceSession(**session_data)
                    session.add(new_session)
                    session.commit()
                    session_id = new_session.id
                    
                    self.active_sessions[name] = {
                        'start_time': now,
                        'last_seen': now,
                        'camera_id': camera_id,
                        'db_id': session_id
                    }
                except Exception as e:
                    logger.error(f"Failed to create attendance session: {e}")
                finally:
                    session.close()

    def check_timeouts(self):
        """Check for sessions that have timed out."""
        now = time.time()
        to_remove = []
        
        with self.lock:
            for name, data in self.active_sessions.items():
                if now - data['last_seen'] > self.timeout:
                    # Close session
                    duration = data['last_seen'] - data['start_time']
                    logger.info(f"Session closed for {name}. Duration: {duration:.1f}s")
                    
                    # Update DB
                    session = self.db.get_session()
                    try:
                        from core.database import AttendanceSession
                        db_session = session.query(AttendanceSession).filter_by(id=data['db_id']).first()
                        if db_session:
                            db_session.exit_time = datetime.fromtimestamp(data['last_seen'])
                            db_session.total_seconds = duration
                            db_session.is_active = False
                            session.commit()
                    except Exception as e:
                        logger.error(f"Failed to close session: {e}")
                    finally:
                        session.close()
                        
                    to_remove.append(name)
            
            for name in to_remove:
                del self.active_sessions[name]
