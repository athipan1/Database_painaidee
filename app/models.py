from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Attraction(db.Model):
    """Model for storing attraction data."""
    __tablename__ = 'attractions'
    
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.Integer, unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, nullable=True)
    # Geocoding fields
    province = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    geocoded = db.Column(db.Boolean, default=False)
    # AI-powered fields
    ai_summary = db.Column(db.Text, nullable=True)  # AI-generated summary
    ai_tags = db.Column(db.Text, nullable=True)  # JSON string of AI-generated tags
    popularity_score = db.Column(db.Float, default=0.0)  # AI-calculated popularity score
    ai_processed = db.Column(db.Boolean, default=False)  # Whether AI processing is complete
    # Full-text search
    search_vector = db.Column(db.Text, nullable=True)  # For PostgreSQL tsvector search
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Attraction {self.id}: {self.title}>'
    
    def to_dict(self):
        """Convert attraction to dictionary."""
        import json
        return {
            'id': self.id,
            'external_id': self.external_id,
            'title': self.title,
            'body': self.body,
            'user_id': self.user_id,
            'province': self.province,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'geocoded': self.geocoded,
            'ai_summary': self.ai_summary,
            'ai_tags': json.loads(self.ai_tags) if self.ai_tags else [],
            'popularity_score': self.popularity_score,
            'ai_processed': self.ai_processed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_from_external_data(cls, data):
        """Create attraction from external API data."""
        return cls(
            external_id=data.get('id'),
            title=data.get('title'),
            body=data.get('body'),
            user_id=data.get('userId'),
            province=data.get('province'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            geocoded=data.get('geocoded', False),
            ai_summary=data.get('ai_summary'),
            ai_tags=data.get('ai_tags'),
            popularity_score=data.get('popularity_score', 0.0),
            ai_processed=data.get('ai_processed', False)
        )


class AttractionHistory(db.Model):
    """Model for storing historical versions of attraction data."""
    __tablename__ = 'attractions_history'
    
    id = db.Column(db.Integer, primary_key=True)
    attraction_id = db.Column(db.Integer, db.ForeignKey('attractions.id'), nullable=False)
    external_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, nullable=True)
    province = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    geocoded = db.Column(db.Boolean, default=False)
    version_number = db.Column(db.Integer, nullable=False)
    archived_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AttractionHistory {self.attraction_id} v{self.version_number}>'
    
    def to_dict(self):
        """Convert attraction history to dictionary."""
        return {
            'id': self.id,
            'attraction_id': self.attraction_id,
            'external_id': self.external_id,
            'title': self.title,
            'body': self.body,
            'user_id': self.user_id,
            'province': self.province,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'geocoded': self.geocoded,
            'version_number': self.version_number,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None
        }


class SyncStatistics(db.Model):
    """Model for storing ETL sync statistics."""
    __tablename__ = 'sync_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    sync_date = db.Column(db.Date, nullable=False)
    total_processed = db.Column(db.Integer, default=0)
    total_saved = db.Column(db.Integer, default=0)
    total_skipped = db.Column(db.Integer, default=0)
    total_errors = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)
    processing_time_seconds = db.Column(db.Float, default=0.0)
    api_source = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SyncStatistics {self.sync_date}: {self.total_processed} processed>'
    
    def to_dict(self):
        """Convert sync statistics to dictionary."""
        return {
            'id': self.id,
            'sync_date': self.sync_date.isoformat() if self.sync_date else None,
            'total_processed': self.total_processed,
            'total_saved': self.total_saved,
            'total_skipped': self.total_skipped,
            'total_errors': self.total_errors,
            'success_rate': self.success_rate,
            'processing_time_seconds': self.processing_time_seconds,
            'api_source': self.api_source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }