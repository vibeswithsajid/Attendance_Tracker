import threading
import queue
import time
import os
import cv2
from loguru import logger
import pygame

class AlertSystem:
    def __init__(self, config):
        self.config = config
        self.alert_queue = queue.Queue()
        self.running = False
        self.last_alert = {} # name -> timestamp
        
        # Audio setup
        if config['alerts']['audio_enabled']:
            try:
                pygame.mixer.init()
                self.sound = pygame.mixer.Sound(config['alerts']['sound_file'])
            except Exception as e:
                logger.warning(f"Audio init failed: {e}")
                self.sound = None
        
        # Telegram setup
        self.telegram_enabled = config['telegram']['enabled']
        if self.telegram_enabled:
            # We would initialize the bot here
            # For now, we'll just log it
            pass

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._process_queue)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def trigger_alert(self, detection, frame, camera_name):
        name = detection['name']
        if name == "Unknown":
            return

        # Rate limit
        now = time.time()
        if name in self.last_alert:
            if now - self.last_alert[name] < self.config['telegram']['rate_limit']:
                return
        
        self.last_alert[name] = now
        self.alert_queue.put({
            'type': 'recognition',
            'data': detection,
            'frame': frame.copy() if frame is not None else None,
            'camera': camera_name,
            'time': now
        })

    def _process_queue(self):
        while self.running:
            try:
                alert = self.alert_queue.get(timeout=1)
                self._handle_alert(alert)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Alert processing error: {e}")

    def _handle_alert(self, alert):
        logger.info(f"Processing alert: {alert['data']['name']} on {alert['camera']}")
        
        # 1. Audio
        if self.config['alerts']['audio_enabled'] and self.sound:
            self.sound.play()
            
        # 2. Screenshot
        if self.config['alerts']['screenshot_enabled'] and alert['frame'] is not None:
            filename = f"{int(alert['time'])}_{alert['data']['name']}.jpg"
            path = os.path.join(self.config['directories']['screenshots'], filename)
            cv2.imwrite(path, alert['frame'])
            
        # 3. Telegram (Placeholder)
        if self.telegram_enabled:
            # Send photo and caption
            pass
