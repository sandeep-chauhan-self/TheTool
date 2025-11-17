"""
Rollback Manager

Part 5B: Deterministic Refactoring Blueprint Engine (DRBE)
Manages rollback points for safe recovery from failed migrations.
"""

import os
import shutil
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class RollbackPoint:
    """
    Snapshot for rollback
    
    Attributes:
        id: Unique identifier
        name: Human-readable name
        description: What this rollback point represents
        timestamp: When this point was created
        files: Dict mapping file paths to backup paths
        metadata: Additional metadata
    """
    id: str
    name: str
    description: str
    timestamp: datetime
    files: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RollbackPoint':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
    
    def __str__(self) -> str:
        """Human-readable summary"""
        lines = [
            f"Rollback Point: {self.name} ({self.id})",
            f"  Created: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Files backed up: {len(self.files)}",
            f"  Description: {self.description}"
        ]
        return "\n".join(lines)


def create_rollback_point(
    name: str,
    description: str,
    files: List[str],
    rollback_dir: str = ".rollback",
    metadata: Optional[Dict[str, Any]] = None
) -> RollbackPoint:
    """
    Create a rollback point by backing up files
    
    Args:
        name: Rollback point name
        description: What this represents
        files: List of file paths to backup
        rollback_dir: Directory to store backups
        metadata: Additional metadata to store
    
    Returns:
        RollbackPoint instance
    
    Usage:
        # Before risky migration
        rollback = create_rollback_point(
            "before_indicator_refactor",
            "Backup before migrating indicators to class-based",
            files=[
                "backend/indicators/rsi.py",
                "backend/indicators/macd.py"
            ]
        )
        
        try:
            # ... perform migration ...
            pass
        except Exception as e:
            # Rollback if failed
            rollback_to_point(rollback)
    """
    # Create rollback directory
    rollback_path = Path(rollback_dir)
    rollback_path.mkdir(exist_ok=True)
    
    # Generate unique ID
    timestamp = datetime.now()
    rollback_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{name.replace(' ', '_')}"
    
    # Create subdirectory for this rollback point
    point_dir = rollback_path / rollback_id
    point_dir.mkdir(exist_ok=True)
    
    # Backup files
    backed_up_files = {}
    
    for file_path in files:
        source = Path(file_path)
        
        if not source.exists():
            logger.warning(f"File not found, skipping: {file_path}")
            continue
        
        # Preserve directory structure in backup
        relative_path = source.name if source.is_file() else source.parts[-1]
        backup_path = point_dir / relative_path
        
        try:
            if source.is_file():
                shutil.copy2(source, backup_path)
            elif source.is_dir():
                shutil.copytree(source, backup_path, dirs_exist_ok=True)
            
            backed_up_files[str(source)] = str(backup_path)
            logger.info(f"Backed up: {source} -> {backup_path}")
        
        except Exception as e:
            logger.error(f"Failed to backup {source}: {e}")
    
    # Create rollback point
    point = RollbackPoint(
        id=rollback_id,
        name=name,
        description=description,
        timestamp=timestamp,
        files=backed_up_files,
        metadata=metadata or {}
    )
    
    # Save metadata
    metadata_file = point_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(point.to_dict(), f, indent=2)
    
    logger.info(f"Created rollback point: {rollback_id} ({len(backed_up_files)} files)")
    
    return point


def rollback_to_point(
    rollback_point: RollbackPoint,
    confirm: bool = True
) -> bool:
    """
    Restore files from a rollback point
    
    Args:
        rollback_point: RollbackPoint to restore
        confirm: If True, log confirmation before restoring
    
    Returns:
        True if successful, False if any errors
    
    Usage:
        # List available rollback points
        points = list_rollback_points()
        
        # Select and restore
        point = points[0]
        success = rollback_to_point(point)
        
        if success:
            print("Rollback successful")
        else:
            print("Rollback had errors")
    """
    if confirm:
        logger.info(f"Rolling back to: {rollback_point.name} ({rollback_point.id})")
        logger.info(f"This will restore {len(rollback_point.files)} files")
    
    success = True
    
    for original_path, backup_path in rollback_point.files.items():
        try:
            source = Path(backup_path)
            dest = Path(original_path)
            
            if not source.exists():
                logger.error(f"Backup not found: {backup_path}")
                success = False
                continue
            
            # Create parent directory if needed
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Restore file
            if source.is_file():
                shutil.copy2(source, dest)
            elif source.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(source, dest)
            
            logger.info(f"Restored: {original_path}")
        
        except Exception as e:
            logger.error(f"Failed to restore {original_path}: {e}")
            success = False
    
    if success:
        logger.info(f"Rollback successful: {rollback_point.name}")
    else:
        logger.warning(f"Rollback completed with errors: {rollback_point.name}")
    
    return success


def list_rollback_points(rollback_dir: str = ".rollback") -> List[RollbackPoint]:
    """
    List all available rollback points
    
    Args:
        rollback_dir: Directory containing rollback points
    
    Returns:
        List of RollbackPoint instances, sorted by timestamp (newest first)
    
    Usage:
        points = list_rollback_points()
        
        print(f"Found {len(points)} rollback points:")
        for i, point in enumerate(points, 1):
            print(f"{i}. {point.name} - {point.timestamp}")
    """
    rollback_path = Path(rollback_dir)
    
    if not rollback_path.exists():
        return []
    
    points = []
    
    # Find all rollback point directories
    for point_dir in rollback_path.iterdir():
        if not point_dir.is_dir():
            continue
        
        metadata_file = point_dir / "metadata.json"
        
        if not metadata_file.exists():
            logger.warning(f"No metadata found in {point_dir}")
            continue
        
        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)
            
            point = RollbackPoint.from_dict(data)
            points.append(point)
        
        except Exception as e:
            logger.error(f"Failed to load rollback point from {point_dir}: {e}")
    
    # Sort by timestamp, newest first
    points.sort(key=lambda p: p.timestamp, reverse=True)
    
    return points


def delete_rollback_point(
    rollback_point: RollbackPoint,
    rollback_dir: str = ".rollback"
) -> bool:
    """
    Delete a rollback point to free space
    
    Args:
        rollback_point: RollbackPoint to delete
        rollback_dir: Directory containing rollback points
    
    Returns:
        True if successful
    
    Usage:
        points = list_rollback_points()
        
        # Delete old rollback points
        for point in points[10:]:  # Keep only 10 most recent
            delete_rollback_point(point)
    """
    point_dir = Path(rollback_dir) / rollback_point.id
    
    if not point_dir.exists():
        logger.warning(f"Rollback point directory not found: {point_dir}")
        return False
    
    try:
        shutil.rmtree(point_dir)
        logger.info(f"Deleted rollback point: {rollback_point.name}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to delete rollback point: {e}")
        return False


def cleanup_old_rollback_points(
    rollback_dir: str = ".rollback",
    keep_count: int = 10,
    max_age_days: Optional[int] = None
) -> int:
    """
    Clean up old rollback points
    
    Args:
        rollback_dir: Directory containing rollback points
        keep_count: Minimum number of points to keep
        max_age_days: Delete points older than this (optional)
    
    Returns:
        Number of points deleted
    
    Usage:
        # Keep last 10 rollback points
        deleted = cleanup_old_rollback_points(keep_count=10)
        print(f"Deleted {deleted} old rollback points")
        
        # Delete points older than 30 days
        deleted = cleanup_old_rollback_points(max_age_days=30)
    """
    points = list_rollback_points(rollback_dir)
    
    if len(points) <= keep_count:
        return 0
    
    deleted_count = 0
    
    # Delete oldest points beyond keep_count
    for point in points[keep_count:]:
        # Check age if max_age_days specified
        if max_age_days:
            age = (datetime.now() - point.timestamp).days
            if age < max_age_days:
                continue
        
        if delete_rollback_point(point, rollback_dir):
            deleted_count += 1
    
    logger.info(f"Cleaned up {deleted_count} old rollback points")
    
    return deleted_count


def get_rollback_disk_usage(rollback_dir: str = ".rollback") -> Dict[str, Any]:
    """
    Calculate disk space used by rollback points
    
    Args:
        rollback_dir: Directory containing rollback points
    
    Returns:
        Dict with disk usage statistics
    
    Usage:
        usage = get_rollback_disk_usage()
        print(f"Rollback points using {usage['total_mb']:.2f} MB")
        print(f"Largest point: {usage['largest_point']} ({usage['largest_mb']:.2f} MB)")
    """
    rollback_path = Path(rollback_dir)
    
    if not rollback_path.exists():
        return {
            'total_bytes': 0,
            'total_mb': 0.0,
            'total_gb': 0.0,
            'point_count': 0
        }
    
    total_bytes = 0
    largest_size = 0
    largest_point = None
    
    for point_dir in rollback_path.iterdir():
        if not point_dir.is_dir():
            continue
        
        # Calculate directory size
        dir_size = sum(
            f.stat().st_size 
            for f in point_dir.rglob('*') 
            if f.is_file()
        )
        
        total_bytes += dir_size
        
        if dir_size > largest_size:
            largest_size = dir_size
            largest_point = point_dir.name
    
    return {
        'total_bytes': total_bytes,
        'total_mb': total_bytes / (1024 * 1024),
        'total_gb': total_bytes / (1024 * 1024 * 1024),
        'point_count': len(list(rollback_path.iterdir())),
        'largest_point': largest_point,
        'largest_mb': largest_size / (1024 * 1024)
    }
