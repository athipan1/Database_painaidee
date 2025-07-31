from datetime import datetime
import hashlib
import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class SyncLog(db.Model):
    """Model for tracking sync operation history."""
    __tablename__ = 'sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    sync_type = db.Column(db.String(50), nullable=False)  # 'daily', 'update', 'manual'
    api_source = db.Column(db.String(100), nullable=False)  # API source name
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='running')  # 'running', 'completed', 'failed'
    total_fetched = db.Column(db.Integer, default=0)
    total_saved = db.Column(db.Integer, default=0)
    total_skipped = db.Column(db.Integer, default=0)
    errors = db.Column(db.Text, nullable=True)  # JSON string of error messages
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SyncLog {self.id}: {self.sync_type} - {self.status}>'
    
    def to_dict(self):
        """Convert sync log to dictionary."""
        return {
            'id': self.id,
            'sync_type': self.sync_type,
            'api_source': self.api_source,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'total_fetched': self.total_fetched,
            'total_saved': self.total_saved,
            'total_skipped': self.total_skipped,
            'errors': self.errors,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def mark_completed(self, total_fetched=0, total_saved=0, total_skipped=0, errors=None):
        """Mark sync as completed with results."""
        self.end_time = datetime.utcnow()
        self.status = 'completed'
        self.total_fetched = total_fetched
        self.total_saved = total_saved
        self.total_skipped = total_skipped
        if errors:
            self.errors = json.dumps(errors) if isinstance(errors, list) else errors
        db.session.commit()
    
    def mark_failed(self, error_message):
        """Mark sync as failed with error message."""
        self.end_time = datetime.utcnow()
        self.status = 'failed'
        self.errors = error_message
        db.session.commit()


class Attraction(db.Model):
    """Model for storing attraction data."""
    __tablename__ = 'attractions'
    
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.Integer, unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, nullable=True)
    content_hash = db.Column(db.String(64), nullable=True, index=True)  # SHA-256 hash for duplicate detection
    location_category = db.Column(db.String(50), nullable=True)  # 'วัด', 'ภูเขา', 'ทะเล', etc.
    province = db.Column(db.String(100), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    original_date = db.Column(db.String(50), nullable=True)  # Original date format from API
    normalized_date = db.Column(db.Date, nullable=True)  # Normalized date in YYYY-MM-DD
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Attraction {self.id}: {self.title}>'
    
    def to_dict(self):
        """Convert attraction to dictionary."""
        return {
            'id': self.id,
            'external_id': self.external_id,
            'title': self.title,
            'body': self.body,
            'user_id': self.user_id,
            'content_hash': self.content_hash,
            'location_category': self.location_category,
            'province': self.province,
            'district': self.district,
            'original_date': self.original_date,
            'normalized_date': self.normalized_date.isoformat() if self.normalized_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def generate_content_hash(self):
        """Generate SHA-256 hash of the content for duplicate detection."""
        content_data = {
            'external_id': self.external_id,
            'title': self.title,
            'body': self.body,
            'user_id': self.user_id
        }
        content_json = json.dumps(content_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content_json.encode('utf-8')).hexdigest()
    
    @classmethod
    def create_from_external_data(cls, data):
        """Create attraction from external API data."""
        attraction = cls(
            external_id=data.get('id'),
            title=data.get('title'),
            body=data.get('body'),
            user_id=data.get('userId'),
            original_date=data.get('date'),  # Store original date format
        )
        # Generate content hash
        attraction.content_hash = attraction.generate_content_hash()
        return attraction
    
    @classmethod
    def find_duplicate_by_hash(cls, content_hash):
        """Find duplicate attraction by content hash."""
        return cls.query.filter_by(content_hash=content_hash).first()
    
    @classmethod
    def find_duplicate_by_external_id(cls, external_id):
        """Find duplicate attraction by external ID."""
        return cls.query.filter_by(external_id=external_id).first()