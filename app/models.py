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
    # AI Features
    keywords = db.Column(db.Text, nullable=True)  # JSON string of extracted keywords
    keywords_extracted = db.Column(db.Boolean, default=False)
    content_rewritten = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)  # For trend analysis
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
            'province': self.province,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'geocoded': self.geocoded,
            'keywords': self.keywords,
            'keywords_extracted': self.keywords_extracted,
            'content_rewritten': self.content_rewritten,
            'view_count': self.view_count,
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
            geocoded=data.get('geocoded', False)
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


class UserInteraction(db.Model):
    """Model for tracking user interactions for personalized recommendations."""
    __tablename__ = 'user_interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)  # Can be session ID or user ID
    attraction_id = db.Column(db.Integer, db.ForeignKey('attractions.id'), nullable=False)
    interaction_type = db.Column(db.String(50), nullable=False)  # 'view', 'click', 'like', etc.
    interaction_value = db.Column(db.Float, default=1.0)  # Weight of the interaction
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    attraction = db.relationship('Attraction', backref='interactions')
    
    def __repr__(self):
        return f'<UserInteraction {self.user_id} -> {self.attraction_id}>'
    
    def to_dict(self):
        """Convert user interaction to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'attraction_id': self.attraction_id,
            'interaction_type': self.interaction_type,
            'interaction_value': self.interaction_value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ConversationSession(db.Model):
    """Model for managing conversational AI sessions and context."""
    __tablename__ = 'conversation_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.String(100), nullable=True)  # Optional user association
    context_data = db.Column(db.Text, nullable=True)  # JSON string of conversation context
    last_intent = db.Column(db.String(100), nullable=True)  # Last detected intent
    preferences = db.Column(db.Text, nullable=True)  # JSON string of user preferences
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # Session expiration
    
    def __repr__(self):
        return f'<ConversationSession {self.session_id}>'
    
    def to_dict(self):
        """Convert conversation session to dictionary."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'context_data': self.context_data,
            'last_intent': self.last_intent,
            'preferences': self.preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }