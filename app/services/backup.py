"""
Backup service for database snapshots and rollback functionality.
"""
import logging
import os
import subprocess
import datetime
from pathlib import Path
from typing import Optional, List
import shutil

logger = logging.getLogger(__name__)


class BackupService:
    """Service for database backup and restore operations."""
    
    def __init__(self, db_url: str, backup_dir: str = "/tmp/db_backups"):
        """
        Initialize backup service.
        
        Args:
            db_url: Database connection URL
            backup_dir: Directory to store backup files
        """
        self.db_url = db_url
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Parse database URL for pg_dump
        self._parse_db_url()
        
        logger.info(f"BackupService initialized with backup directory: {self.backup_dir}")
    
    def _parse_db_url(self):
        """Parse database URL to extract connection parameters."""
        try:
            # Handle postgresql:// URLs
            if self.db_url.startswith('postgresql://'):
                from urllib.parse import urlparse
                parsed = urlparse(self.db_url)
                
                self.db_host = parsed.hostname
                self.db_port = parsed.port or 5432
                self.db_name = parsed.path.lstrip('/')
                self.db_user = parsed.username
                self.db_password = parsed.password
            else:
                # Fallback for environment variables
                self.db_host = os.getenv('POSTGRES_HOST', 'localhost')
                self.db_port = int(os.getenv('POSTGRES_PORT', 5432))
                self.db_name = os.getenv('POSTGRES_DB', 'painaidee_db')
                self.db_user = os.getenv('POSTGRES_USER', 'user')
                self.db_password = os.getenv('POSTGRES_PASSWORD', 'password')
                
        except Exception as e:
            logger.error(f"Failed to parse database URL: {str(e)}")
            raise
    
    def create_backup(self, backup_name: str = None) -> Optional[str]:
        """
        Create a database backup using pg_dump.
        
        Args:
            backup_name: Custom backup name (optional)
            
        Returns:
            Path to backup file or None if failed
        """
        try:
            if not backup_name:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"painaidee_backup_{timestamp}.sql"
            
            backup_path = self.backup_dir / backup_name
            
            # Prepare pg_dump command
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            cmd = [
                'pg_dump',
                '-h', str(self.db_host),
                '-p', str(self.db_port),
                '-U', self.db_user,
                '-d', self.db_name,
                '--no-password',
                '--verbose',
                '--clean',
                '--create',
                '-f', str(backup_path)
            ]
            
            logger.info(f"Creating backup: {backup_path}")
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Backup created successfully: {backup_path}")
                return str(backup_path)
            else:
                logger.error(f"pg_dump failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Backup operation timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return None
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore database from backup file.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not Path(backup_path).exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Prepare psql command
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            cmd = [
                'psql',
                '-h', str(self.db_host),
                '-p', str(self.db_port),
                '-U', self.db_user,
                '-d', self.db_name,
                '--no-password',
                '-f', backup_path
            ]
            
            logger.info(f"Restoring from backup: {backup_path}")
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Database restored successfully from: {backup_path}")
                return True
            else:
                logger.error(f"Restore failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Restore operation timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to restore backup: {str(e)}")
            return False
    
    def list_backups(self) -> List[dict]:
        """
        List available backup files.
        
        Returns:
            List of backup file information dictionaries
        """
        try:
            backups = []
            
            for backup_file in self.backup_dir.glob("*.sql"):
                stat = backup_file.stat()
                backups.append({
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'size': stat.st_size,
                    'created': datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            # Sort by creation time, newest first
            backups.sort(key=lambda x: x['created'], reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {str(e)}")
            return []
    
    def delete_backup(self, backup_name: str) -> bool:
        """
        Delete a backup file.
        
        Args:
            backup_name: Name of backup file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            backup_path = self.backup_dir / backup_name
            
            if backup_path.exists():
                backup_path.unlink()
                logger.info(f"Deleted backup: {backup_name}")
                return True
            else:
                logger.warning(f"Backup file not found: {backup_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_name}: {str(e)}")
            return False
    
    def cleanup_old_backups(self, keep_backups: int = 7) -> int:
        """
        Clean up old backup files, keeping only the specified number.
        
        Args:
            keep_backups: Number of recent backups to keep
            
        Returns:
            Number of backups deleted
        """
        try:
            backups = self.list_backups()
            
            if len(backups) <= keep_backups:
                return 0
            
            # Delete old backups
            backups_to_delete = backups[keep_backups:]
            deleted_count = 0
            
            for backup in backups_to_delete:
                if self.delete_backup(backup['name']):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old backups")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {str(e)}")
            return 0
    
    def create_pre_sync_backup(self) -> Optional[str]:
        """
        Create a backup before ETL sync operation.
        
        Returns:
            Path to backup file or None if failed
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"pre_sync_backup_{timestamp}.sql"
        
        return self.create_backup(backup_name)


# Global backup service instance
_backup_service = None


def get_backup_service(db_url: str = None, backup_dir: str = "/tmp/db_backups") -> BackupService:
    """Get or create global backup service instance."""
    global _backup_service
    
    if _backup_service is None and db_url:
        _backup_service = BackupService(db_url, backup_dir)
    
    return _backup_service