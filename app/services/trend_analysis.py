"""
AI-powered trend analysis service for attraction popularity and heatmap generation.
"""
import json
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from calendar import monthrange

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-GUI backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from app.models import Attraction, UserInteraction, SyncStatistics
from app.services.keyword_extraction import keywords_from_json


class TrendAnalyzer:
    """AI-powered trend analysis for attractions."""
    
    def __init__(self):
        self.use_visualization = MATPLOTLIB_AVAILABLE
    
    def analyze_popularity_trends(
        self, 
        days: int = 30, 
        province: Optional[str] = None
    ) -> Dict:
        """
        Analyze popularity trends over time.
        
        Args:
            days: Number of days to analyze
            province: Optional province filter
            
        Returns:
            Dictionary containing trend analysis data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get interactions within the time period
        query = UserInteraction.query.filter(
            UserInteraction.created_at >= start_date,
            UserInteraction.created_at <= end_date
        )
        
        if province:
            query = query.join(Attraction).filter(Attraction.province == province)
        
        interactions = query.all()
        
        # Analyze trends
        daily_trends = self._analyze_daily_trends(interactions, start_date, end_date)
        keyword_trends = self._analyze_keyword_trends(interactions)
        province_trends = self._analyze_province_trends(interactions)
        seasonal_patterns = self._analyze_seasonal_patterns(interactions)
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'daily_trends': daily_trends,
            'keyword_trends': keyword_trends,
            'province_trends': province_trends,
            'seasonal_patterns': seasonal_patterns,
            'total_interactions': len(interactions)
        }
    
    def _analyze_daily_trends(
        self, 
        interactions: List[UserInteraction], 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict]:
        """Analyze daily interaction trends."""
        daily_counts = defaultdict(int)
        daily_unique_users = defaultdict(set)
        daily_attractions = defaultdict(set)
        
        for interaction in interactions:
            date_key = interaction.created_at.date().isoformat()
            daily_counts[date_key] += 1
            daily_unique_users[date_key].add(interaction.user_id)
            daily_attractions[date_key].add(interaction.attraction_id)
        
        # Generate daily trend data
        trends = []
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_key = current_date.isoformat()
            trends.append({
                'date': date_key,
                'interactions': daily_counts[date_key],
                'unique_users': len(daily_unique_users[date_key]),
                'unique_attractions': len(daily_attractions[date_key])
            })
            current_date += timedelta(days=1)
        
        return trends
    
    def _analyze_keyword_trends(self, interactions: List[UserInteraction]) -> List[Dict]:
        """Analyze trending keywords from popular attractions."""
        keyword_counts = Counter()
        keyword_interactions = defaultdict(int)
        
        for interaction in interactions:
            if interaction.attraction and interaction.attraction.keywords:
                keywords = keywords_from_json(interaction.attraction.keywords)
                for keyword in keywords:
                    keyword_counts[keyword] += 1
                    keyword_interactions[keyword] += interaction.interaction_value
        
        # Calculate trending keywords
        trending_keywords = []
        for keyword, count in keyword_counts.most_common(20):
            avg_interaction = keyword_interactions[keyword] / count if count > 0 else 0
            trending_keywords.append({
                'keyword': keyword,
                'count': count,
                'avg_interaction_value': round(avg_interaction, 2),
                'trend_score': count * avg_interaction
            })
        
        # Sort by trend score
        trending_keywords.sort(key=lambda x: x['trend_score'], reverse=True)
        return trending_keywords[:10]
    
    def _analyze_province_trends(self, interactions: List[UserInteraction]) -> List[Dict]:
        """Analyze trends by province."""
        province_data = defaultdict(lambda: {
            'interactions': 0,
            'unique_users': set(),
            'attractions': set(),
            'total_interaction_value': 0
        })
        
        for interaction in interactions:
            if interaction.attraction and interaction.attraction.province:
                province = interaction.attraction.province
                province_data[province]['interactions'] += 1
                province_data[province]['unique_users'].add(interaction.user_id)
                province_data[province]['attractions'].add(interaction.attraction_id)
                province_data[province]['total_interaction_value'] += interaction.interaction_value
        
        # Convert to list and calculate metrics
        province_trends = []
        for province, data in province_data.items():
            unique_users = len(data['unique_users'])
            unique_attractions = len(data['attractions'])
            avg_interaction = data['total_interaction_value'] / data['interactions'] if data['interactions'] > 0 else 0
            
            province_trends.append({
                'province': province,
                'interactions': data['interactions'],
                'unique_users': unique_users,
                'unique_attractions': unique_attractions,
                'avg_interaction_value': round(avg_interaction, 2),
                'popularity_score': data['interactions'] * avg_interaction
            })
        
        # Sort by popularity score
        province_trends.sort(key=lambda x: x['popularity_score'], reverse=True)
        return province_trends
    
    def _analyze_seasonal_patterns(self, interactions: List[UserInteraction]) -> Dict:
        """Analyze seasonal patterns in interactions."""
        monthly_data = defaultdict(int)
        weekday_data = defaultdict(int)
        hourly_data = defaultdict(int)
        
        for interaction in interactions:
            # Monthly patterns
            month_key = interaction.created_at.strftime('%Y-%m')
            monthly_data[month_key] += 1
            
            # Weekday patterns (0=Monday, 6=Sunday)
            weekday = interaction.created_at.weekday()
            weekday_data[weekday] += 1
            
            # Hourly patterns
            hour = interaction.created_at.hour
            hourly_data[hour] += 1
        
        # Convert to lists for easier consumption
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        return {
            'monthly_patterns': dict(monthly_data),
            'weekday_patterns': [
                {'weekday': weekday_names[i], 'interactions': weekday_data[i]}
                for i in range(7)
            ],
            'hourly_patterns': [
                {'hour': hour, 'interactions': hourly_data[hour]}
                for hour in range(24)
            ]
        }
    
    def generate_heatmap_data(
        self, 
        days: int = 30, 
        grid_size: int = 20
    ) -> Dict:
        """
        Generate heatmap data for attraction popularity by geographic region.
        
        Args:
            days: Number of days to analyze
            grid_size: Size of the geographic grid
            
        Returns:
            Heatmap data with coordinates and intensity values
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get interactions with geographic data
        interactions = UserInteraction.query.join(Attraction).filter(
            UserInteraction.created_at >= start_date,
            UserInteraction.created_at <= end_date,
            Attraction.latitude.isnot(None),
            Attraction.longitude.isnot(None)
        ).all()
        
        if not interactions:
            return {
                'grid_data': [],
                'bounds': None,
                'total_interactions': 0
            }
        
        # Get coordinate bounds
        latitudes = [interaction.attraction.latitude for interaction in interactions]
        longitudes = [interaction.attraction.longitude for interaction in interactions]
        
        min_lat, max_lat = min(latitudes), max(latitudes)
        min_lon, max_lon = min(longitudes), max(longitudes)
        
        # Create grid
        lat_step = (max_lat - min_lat) / grid_size
        lon_step = (max_lon - min_lon) / grid_size
        
        grid_data = []
        for i in range(grid_size):
            for j in range(grid_size):
                grid_lat = min_lat + i * lat_step
                grid_lon = min_lon + j * lon_step
                
                # Count interactions in this grid cell
                intensity = 0
                for interaction in interactions:
                    attr_lat = interaction.attraction.latitude
                    attr_lon = interaction.attraction.longitude
                    
                    if (grid_lat <= attr_lat < grid_lat + lat_step and
                        grid_lon <= attr_lon < grid_lon + lon_step):
                        intensity += interaction.interaction_value
                
                if intensity > 0:
                    grid_data.append({
                        'latitude': grid_lat + lat_step / 2,
                        'longitude': grid_lon + lon_step / 2,
                        'intensity': intensity
                    })
        
        return {
            'grid_data': grid_data,
            'bounds': {
                'min_latitude': min_lat,
                'max_latitude': max_lat,
                'min_longitude': min_lon,
                'max_longitude': max_lon
            },
            'total_interactions': len(interactions)
        }
    
    def predict_future_trends(self, days_ahead: int = 7) -> Dict:
        """
        Predict future trends based on historical data.
        
        Args:
            days_ahead: Number of days to predict ahead
            
        Returns:
            Prediction data
        """
        # Simple trend prediction based on historical averages
        # In a real implementation, you might use more sophisticated ML models
        
        # Get last 30 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        interactions = UserInteraction.query.filter(
            UserInteraction.created_at >= start_date,
            UserInteraction.created_at <= end_date
        ).all()
        
        if not interactions:
            return {
                'predictions': [],
                'confidence': 0.0
            }
        
        # Calculate daily averages
        daily_counts = defaultdict(int)
        for interaction in interactions:
            date_key = interaction.created_at.date()
            daily_counts[date_key] += 1
        
        # Calculate moving average
        daily_values = list(daily_counts.values())
        if len(daily_values) >= 7:
            recent_avg = sum(daily_values[-7:]) / 7  # Last 7 days average
            overall_avg = sum(daily_values) / len(daily_values)  # Overall average
            
            # Simple trend calculation
            trend_multiplier = recent_avg / overall_avg if overall_avg > 0 else 1.0
        else:
            overall_avg = sum(daily_values) / len(daily_values) if daily_values else 0
            trend_multiplier = 1.0
        
        # Generate predictions
        predictions = []
        base_date = end_date.date()
        
        for i in range(1, days_ahead + 1):
            pred_date = base_date + timedelta(days=i)
            
            # Apply weekly seasonality (simple model)
            weekday = pred_date.weekday()
            weekday_multiplier = {
                0: 0.9,  # Monday
                1: 0.95, # Tuesday
                2: 1.0,  # Wednesday
                3: 1.0,  # Thursday
                4: 1.1,  # Friday
                5: 1.3,  # Saturday
                6: 1.2   # Sunday
            }.get(weekday, 1.0)
            
            predicted_value = overall_avg * trend_multiplier * weekday_multiplier
            
            predictions.append({
                'date': pred_date.isoformat(),
                'predicted_interactions': max(0, int(predicted_value)),
                'weekday': pred_date.strftime('%A'),
                'confidence': 0.7  # Simple confidence score
            })
        
        return {
            'predictions': predictions,
            'confidence': 0.7,
            'model_info': 'Simple moving average with seasonal adjustment'
        }
    
    def get_top_attractions_by_period(
        self, 
        period: str = 'week', 
        province: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get top attractions for a specific time period.
        
        Args:
            period: 'day', 'week', 'month', or 'year'
            province: Optional province filter
            limit: Maximum number of attractions to return
            
        Returns:
            List of top attractions with stats
        """
        # Calculate date range based on period
        end_date = datetime.now()
        if period == 'day':
            start_date = end_date - timedelta(days=1)
        elif period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=7)  # Default to week
        
        # Query interactions
        query = UserInteraction.query.filter(
            UserInteraction.created_at >= start_date,
            UserInteraction.created_at <= end_date
        ).join(Attraction)
        
        if province:
            query = query.filter(Attraction.province == province)
        
        interactions = query.all()
        
        # Aggregate by attraction
        attraction_stats = defaultdict(lambda: {
            'interactions': 0,
            'unique_users': set(),
            'total_value': 0,
            'attraction': None
        })
        
        for interaction in interactions:
            attraction_id = interaction.attraction_id
            attraction_stats[attraction_id]['interactions'] += 1
            attraction_stats[attraction_id]['unique_users'].add(interaction.user_id)
            attraction_stats[attraction_id]['total_value'] += interaction.interaction_value
            attraction_stats[attraction_id]['attraction'] = interaction.attraction
        
        # Convert to list and calculate scores
        top_attractions = []
        for attraction_id, stats in attraction_stats.items():
            if stats['attraction']:
                unique_users = len(stats['unique_users'])
                avg_value = stats['total_value'] / stats['interactions'] if stats['interactions'] > 0 else 0
                
                top_attractions.append({
                    'attraction': stats['attraction'].to_dict(),
                    'interactions': stats['interactions'],
                    'unique_users': unique_users,
                    'avg_interaction_value': round(avg_value, 2),
                    'popularity_score': stats['interactions'] * avg_value
                })
        
        # Sort by popularity score and return top results
        top_attractions.sort(key=lambda x: x['popularity_score'], reverse=True)
        return top_attractions[:limit]


def analyze_attraction_trends(days: int = 30, province: Optional[str] = None) -> Dict:
    """
    Analyze attraction popularity trends.
    
    Args:
        days: Number of days to analyze
        province: Optional province filter
        
    Returns:
        Trend analysis data
    """
    analyzer = TrendAnalyzer()
    return analyzer.analyze_popularity_trends(days, province)


def get_heatmap_data(days: int = 30) -> Dict:
    """
    Get heatmap data for geographic visualization.
    
    Args:
        days: Number of days to analyze
        
    Returns:
        Heatmap data
    """
    analyzer = TrendAnalyzer()
    return analyzer.generate_heatmap_data(days)


def get_trend_predictions(days_ahead: int = 7) -> Dict:
    """
    Get future trend predictions.
    
    Args:
        days_ahead: Number of days to predict
        
    Returns:
        Prediction data
    """
    analyzer = TrendAnalyzer()
    return analyzer.predict_future_trends(days_ahead)