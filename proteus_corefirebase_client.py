"""
Firebase Admin SDK Integration for Project Proteus
Handles Firestore (state) and Realtime Database (queue) operations
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore, db
from firebase_admin.exceptions import FirebaseError

from .config import config

logger = logging.getLogger(__name__)

class FirebaseClient:
    """Singleton Firebase client with connection pooling and error recovery"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = False
            self._firestore_client = None
            self._realtime_db = None
            self._app = None
    
    def initialize(self) -> None:
        """Initialize Firebase connection with retry logic"""
        if self._initialized:
            return
            
        try:
            # Check if Firebase app already exists
            if not firebase_admin._apps:
                cred_path = Path(config.firebase_credentials_path)
                if not cred_path.exists():
                    raise FileNotFoundError(
                        f"Firebase credentials file not found at {cred_path}"
                    )
                
                cred = credentials.Certificate(str(cred_path))
                self._app = firebase_admin.initialize_app(
                    cred,
                    {
                        'databaseURL': f'https://{config.firebase_project_id}.firebaseio.com',
                        'projectId': config.firebase_project_id
                    }
                )
                logger.info(f"Firebase initialized for project: {config.firebase_project_id}")
            else:
                self._app = firebase_admin.get_app()
                logger.info("Using existing Firebase app")
            
            # Initialize clients
            self._firestore_client = firestore.client(app=self._app)
            self._realtime_db = db.reference(app=self._app)
            
            # Test connection
            self._test_connections()
            
            self._initialized = True
            logger.info("Firebase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise
    
    def _test_connections(self) -> None:
        """Test both Firestore and Realtime Database connections"""
        try:
            # Test Firestore
            test_doc = self._firestore_client.collection('_health').document('test')
            test_doc.set({'timestamp': datetime.utcnow().isoformat()})
            test_doc.delete()
            
            # Test Realtime DB
            self._realtime_db.child('_health').set({
                'timestamp': datetime.utcnow().isoformat()
            })
            self._realtime_db.child('_health').delete()
            
            logger.debug("Firebase connections tested successfully")
            
        except Exception as e:
            logger.error(f"Firebase connection test failed: {str(e)}")
            raise
    
    @property
    def firestore(self) -> firestore.Client:
        """Get Firestore client with lazy initialization"""
        if not self._initialized:
            self.initialize()
        return self._firestore_client
    
    @property
    def realtime_db(self) -> db.Reference:
        """Get Realtime Database reference with lazy initialization"""
        if not self._initialized:
            self.initialize()
        return self._realtime_db
    
    def create_job(self, job_data: Dict[str, Any]) -> str:
        """
        Create a new computation job in Firestore
        Returns job_id
        """
        try:
            # Generate job ID
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            job_id = f"job_{timestamp}_{hash(str(job_data)) % 10000:04d}"
            
            # Prepare job document
            job_doc = {
                **job_data,
                'job_id': job_id,
                'status': 'queued',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'attempts': 0,
                'last_error': None
            }
            
            # Store in Firestore
            job_ref = self.firestore.collection