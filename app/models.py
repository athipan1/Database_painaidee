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
    # Data Cleaning & Enrichment fields
    auto_tagged = db.Column(db.Boolean, default=False)
    categorized = db.Column(db.Boolean, default=False)
    data_validated = db.Column(db.Boolean, default=False)
    validation_score = db.Column(db.Float, nullable=True)  # Overall data quality score (0-1)
    last_cleaned_at = db.Column(db.DateTime, nullable=True)
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
            'auto_tagged': self.auto_tagged,
            'categorized': self.categorized,
            'data_validated': self.data_validated,
            'validation_score': self.validation_score,
            'last_cleaned_at': self.last_cleaned_at.isoformat() if self.last_cleaned_at else None,
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
    interaction_type = db.Column(db.String(50), nullable=False)  # 'view', 'click', 'like', 'search', 'favorite', etc.
    interaction_value = db.Column(db.Float, default=1.0)  # Weight of the interaction
    # Enhanced tracking fields
    duration_seconds = db.Column(db.Integer, nullable=True)  # Time spent on attraction
    search_query = db.Column(db.String(200), nullable=True)  # Search query if applicable
    page_url = db.Column(db.String(500), nullable=True)  # URL where interaction occurred
    user_agent = db.Column(db.String(500), nullable=True)  # Browser/device info
    session_id = db.Column(db.String(100), nullable=True)  # Session identifier
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
            'duration_seconds': self.duration_seconds,
            'search_query': self.search_query,
            'page_url': self.page_url,
            'user_agent': self.user_agent,
            'session_id': self.session_id,
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


class UserBehaviorSession(db.Model):
    """Model for tracking user behavior sessions with detailed analytics."""
    __tablename__ = 'user_behavior_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.String(100), nullable=True)  # Optional user association
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    total_duration_seconds = db.Column(db.Integer, default=0)
    page_views = db.Column(db.Integer, default=0)
    interactions_count = db.Column(db.Integer, default=0)
    search_queries_count = db.Column(db.Integer, default=0)
    favorites_count = db.Column(db.Integer, default=0)
    # Device and location info
    user_agent = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 compatible
    device_type = db.Column(db.String(50), nullable=True)  # mobile, desktop, tablet
    # Behavioral patterns
    behavior_pattern = db.Column(db.Text, nullable=True)  # JSON string of detected patterns
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserBehaviorSession {self.session_id}>'
    
    def to_dict(self):
        """Convert user behavior session to dictionary."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_duration_seconds': self.total_duration_seconds,
            'page_views': self.page_views,
            'interactions_count': self.interactions_count,
            'search_queries_count': self.search_queries_count,
            'favorites_count': self.favorites_count,
            'user_agent': self.user_agent,
            'ip_address': self.ip_address,
            'device_type': self.device_type,
            'behavior_pattern': self.behavior_pattern,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SearchQuery(db.Model):
    """Model for tracking search queries and patterns."""
    __tablename__ = 'search_queries'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.String(100), nullable=True)
    query_text = db.Column(db.String(500), nullable=False)
    results_count = db.Column(db.Integer, default=0)
    clicked_results = db.Column(db.Text, nullable=True)  # JSON array of clicked attraction IDs
    search_context = db.Column(db.String(100), nullable=True)  # 'homepage', 'category', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SearchQuery {self.query_text}>'
    
    def to_dict(self):
        """Convert search query to dictionary."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'query_text': self.query_text,
            'results_count': self.results_count,
            'clicked_results': self.clicked_results,
            'search_context': self.search_context,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserPreference(db.Model):
    """Model for storing learned user preferences."""
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    preference_type = db.Column(db.String(50), nullable=False)  # 'category', 'location', 'keyword', etc.
    preference_value = db.Column(db.String(200), nullable=False)
    confidence_score = db.Column(db.Float, default=0.0)  # 0.0 to 1.0
    interaction_count = db.Column(db.Integer, default=1)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'preference_type', 'preference_value'),)
    
    def __repr__(self):
        return f'<UserPreference {self.user_id}: {self.preference_type}={self.preference_value}>'
    
    def to_dict(self):
        """Convert user preference to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'preference_type': self.preference_type,
            'preference_value': self.preference_value,
            'confidence_score': self.confidence_score,
            'interaction_count': self.interaction_count,
            'last_interaction': self.last_interaction.isoformat() if self.last_interaction else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AttractionTag(db.Model):
    """Model for storing auto-generated tags for attractions."""
    __tablename__ = 'attraction_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    attraction_id = db.Column(db.Integer, db.ForeignKey('attractions.id'), nullable=False)
    tag_name = db.Column(db.String(100), nullable=False)
    tag_type = db.Column(db.String(50), nullable=False)  # 'category', 'activity', 'location', 'feature'
    confidence_score = db.Column(db.Float, default=0.0)  # AI confidence in the tag
    source = db.Column(db.String(50), default='ai_auto')  # 'ai_auto', 'manual', 'imported'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    attraction = db.relationship('Attraction', backref='tags')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('attraction_id', 'tag_name', 'tag_type'),)
    
    def __repr__(self):
        return f'<AttractionTag {self.attraction_id}: {self.tag_type}={self.tag_name}>'
    
    def to_dict(self):
        """Convert attraction tag to dictionary."""
        return {
            'id': self.id,
            'attraction_id': self.attraction_id,
            'tag_name': self.tag_name,
            'tag_type': self.tag_type,
            'confidence_score': self.confidence_score,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AttractionCategory(db.Model):
    """Model for AI-suggested categories for attractions."""
    __tablename__ = 'attraction_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    attraction_id = db.Column(db.Integer, db.ForeignKey('attractions.id'), nullable=False)
    category_name = db.Column(db.String(100), nullable=False)
    parent_category = db.Column(db.String(100), nullable=True)  # For hierarchical categories
    confidence_score = db.Column(db.Float, default=0.0)
    is_primary = db.Column(db.Boolean, default=False)  # Main category vs secondary
    source = db.Column(db.String(50), default='ai_suggestion')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    attraction = db.relationship('Attraction', backref='categories')
    
    def __repr__(self):
        return f'<AttractionCategory {self.attraction_id}: {self.category_name}>'
    
    def to_dict(self):
        """Convert attraction category to dictionary."""
        return {
            'id': self.id,
            'attraction_id': self.attraction_id,
            'category_name': self.category_name,
            'parent_category': self.parent_category,
            'confidence_score': self.confidence_score,
            'is_primary': self.is_primary,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DataValidationResult(db.Model):
    """Model for storing data validation results from AI cleaning."""
    __tablename__ = 'data_validation_results'
    
    id = db.Column(db.Integer, primary_key=True)
    attraction_id = db.Column(db.Integer, db.ForeignKey('attractions.id'), nullable=False)
    field_name = db.Column(db.String(50), nullable=False)  # 'title', 'body', etc.
    validation_type = db.Column(db.String(50), nullable=False)  # 'grammar', 'duplicate', 'typo'
    issue_description = db.Column(db.Text, nullable=True)
    suggested_fix = db.Column(db.Text, nullable=True)
    confidence_score = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'fixed', 'ignored'
    fixed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    attraction = db.relationship('Attraction', backref='validation_results')
    
    def __repr__(self):
        return f'<DataValidationResult {self.attraction_id}: {self.validation_type}>'
    
    def to_dict(self):
        """Convert data validation result to dictionary."""
        return {
            'id': self.id,
            'attraction_id': self.attraction_id,
            'field_name': self.field_name,
            'validation_type': self.validation_type,
            'issue_description': self.issue_description,
            'suggested_fix': self.suggested_fix,
            'confidence_score': self.confidence_score,
            'status': self.status,
            'fixed_at': self.fixed_at.isoformat() if self.fixed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }