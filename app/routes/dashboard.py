"""Dashboard routes for monitoring ETL operations and statistics."""
import logging
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, jsonify
from app.models import db, SyncStatistics, Attraction, AttractionHistory

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/')
def dashboard_home():
    """Dashboard home page."""
    return render_template('dashboard.html')


@dashboard_bp.route('/stats')
def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        # Get recent sync statistics (last 30 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        recent_stats = SyncStatistics.query.filter(
            SyncStatistics.sync_date >= start_date,
            SyncStatistics.sync_date <= end_date
        ).order_by(SyncStatistics.sync_date.desc()).all()
        
        # Calculate summary statistics
        total_attractions = Attraction.query.count()
        geocoded_attractions = Attraction.query.filter(Attraction.geocoded == True).count()
        total_versions = AttractionHistory.query.count()
        
        # Today's stats
        today_stats = SyncStatistics.query.filter(
            SyncStatistics.sync_date == end_date
        ).first()
        
        # Last 7 days success rate
        week_start = end_date - timedelta(days=7)
        week_stats = SyncStatistics.query.filter(
            SyncStatistics.sync_date >= week_start,
            SyncStatistics.sync_date <= end_date
        ).all()
        
        avg_success_rate = 0
        avg_processing_time = 0
        if week_stats:
            avg_success_rate = sum(s.success_rate for s in week_stats) / len(week_stats)
            avg_processing_time = sum(s.processing_time_seconds for s in week_stats) / len(week_stats)
        
        # Prepare chart data
        chart_data = {
            'dates': [stat.sync_date.isoformat() for stat in recent_stats[::-1]],  # Reverse for chronological order
            'processed': [stat.total_processed for stat in recent_stats[::-1]],
            'saved': [stat.total_saved for stat in recent_stats[::-1]],
            'errors': [stat.total_errors for stat in recent_stats[::-1]],
            'success_rates': [stat.success_rate for stat in recent_stats[::-1]]
        }
        
        dashboard_data = {
            'summary': {
                'total_attractions': total_attractions,
                'geocoded_attractions': geocoded_attractions,
                'geocoded_percentage': round((geocoded_attractions / total_attractions * 100) if total_attractions > 0 else 0, 1),
                'total_versions': total_versions,
                'avg_success_rate': round(avg_success_rate, 1),
                'avg_processing_time': round(avg_processing_time, 2)
            },
            'today': {
                'processed': today_stats.total_processed if today_stats else 0,
                'saved': today_stats.total_saved if today_stats else 0,
                'errors': today_stats.total_errors if today_stats else 0,
                'success_rate': today_stats.success_rate if today_stats else 0,
                'processing_time': today_stats.processing_time_seconds if today_stats else 0
            },
            'chart_data': chart_data,
            'recent_syncs': [stat.to_dict() for stat in recent_stats[:10]]  # Last 10 syncs
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({'error': 'Failed to load dashboard stats'}), 500


@dashboard_bp.route('/health')
def dashboard_health():
    """Dashboard health check."""
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        
        # Get last sync info
        last_sync = SyncStatistics.query.order_by(
            SyncStatistics.created_at.desc()
        ).first()
        
        health_data = {
            'status': 'healthy',
            'database': 'connected',
            'last_sync': last_sync.created_at.isoformat() if last_sync else None,
            'last_sync_success_rate': last_sync.success_rate if last_sync else None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"Dashboard health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@dashboard_bp.route('/attractions/recent')
def get_recent_attractions():
    """Get recently updated attractions."""
    try:
        limit = 20
        
        recent_attractions = Attraction.query.order_by(
            Attraction.updated_at.desc()
        ).limit(limit).all()
        
        attractions_data = []
        for attraction in recent_attractions:
            attraction_dict = attraction.to_dict()
            
            # Add version count
            version_count = AttractionHistory.query.filter(
                AttractionHistory.attraction_id == attraction.id
            ).count()
            attraction_dict['version_count'] = version_count
            
            attractions_data.append(attraction_dict)
        
        return jsonify({
            'attractions': attractions_data,
            'total_count': len(attractions_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting recent attractions: {str(e)}")
        return jsonify({'error': 'Failed to load recent attractions'}), 500


@dashboard_bp.route('/versions/<int:attraction_id>')
def get_attraction_versions(attraction_id):
    """Get version history for a specific attraction."""
    try:
        versions = AttractionHistory.query.filter(
            AttractionHistory.attraction_id == attraction_id
        ).order_by(AttractionHistory.version_number.desc()).all()
        
        return jsonify([version.to_dict() for version in versions])
        
    except Exception as e:
        logger.error(f"Error getting attraction versions: {str(e)}")
        return jsonify({'error': 'Failed to load attraction versions'}), 500