"""
Database backup tasks - runs in separate process to avoid file locks.

Can be run standalone or scheduled by BackupService.
"""

import argparse
import gzip
import logging
import shutil
import sqlite3
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Standalone logging setup (separate process)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def perform_daily_backup(config: dict):
    """
    Perform daily database backup.

    Steps:
    1. Copy current/*.db to daily/YYYY-MM-DD/
    2. Append to archive/*_all.db (using ATTACH DATABASE)
    3. Compress old daily backups (gzip)
    4. Delete backups older than retention period

    Args:
        config: System configuration dictionary
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting daily backup")
        logger.info("=" * 60)

        db_config = config['database']['sqlite']
        current_dir = Path(db_config['path'])
        daily_dir = Path(config.get('backup', {}).get('daily_path', 'data/databases/daily'))
        archive_dir = Path(config.get('backup', {}).get('archive_path', 'data/databases/archive'))

        # Create backup directories
        daily_dir.mkdir(parents=True, exist_ok=True)
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Today's backup folder
        today = datetime.now().strftime('%Y-%m-%d')
        today_backup_dir = daily_dir / today
        today_backup_dir.mkdir(parents=True, exist_ok=True)

        # 1. Copy current databases to daily backup
        db_files = db_config['databases']
        for db_name, filename in db_files.items():
            source = current_dir / filename
            dest = today_backup_dir / filename

            if source.exists():
                logger.info(f"Copying {filename} to daily backup...")
                shutil.copy2(source, dest)
            else:
                logger.warning(f"Source database not found: {source}")

        # 2. Merge into archive databases
        for db_name, filename in db_files.items():
            daily_db = today_backup_dir / filename
            archive_db = archive_dir / f"{db_name}_all.db"

            if daily_db.exists():
                logger.info(f"Merging {filename} into archive...")
                _merge_database(daily_db, archive_db, db_name)

        # 3. Compress old daily backups
        retention_days = config.get('backup', {}).get('retention_days', 30)
        compress_threshold_days = config.get('backup', {}).get('compress_after_days', 7)

        _compress_old_backups(daily_dir, compress_threshold_days)

        # 4. Delete old backups
        _delete_old_backups(daily_dir, retention_days)

        logger.info("=" * 60)
        logger.info("Daily backup completed successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Backup failed: {e}", exc_info=True)
        raise


def _merge_database(source_db: Path, archive_db: Path, db_name: str):
    """
    Merge source database into archive database.

    Uses ATTACH DATABASE to copy all rows.

    Args:
        source_db: Path to source database
        archive_db: Path to archive database
        db_name: Database name (raw, total, log, ml)
    """
    try:
        # Create archive if doesn't exist
        if not archive_db.exists():
            logger.info(f"Creating new archive: {archive_db}")
            # Copy schema from source
            shutil.copy2(source_db, archive_db)
            return

        # Connect to archive
        conn = sqlite3.connect(str(archive_db))

        try:
            # Attach source database
            conn.execute(f"ATTACH DATABASE '{source_db}' AS source")

            # Get table names
            tables = _get_table_names(db_name)

            # Merge each table
            for table in tables:
                # Get row count before merge
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count_before = cursor.fetchone()[0]

                # Insert rows from source (skip duplicates)
                conn.execute(f"""
                    INSERT OR IGNORE INTO {table}
                    SELECT * FROM source.{table}
                """)

                # Get row count after merge
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count_after = cursor.fetchone()[0]

                rows_added = count_after - count_before
                logger.info(f"  {table}: +{rows_added} rows (total: {count_after})")

            # Commit
            conn.commit()

            # Detach source
            conn.execute("DETACH DATABASE source")

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Error merging database: {e}", exc_info=True)
        raise


def _get_table_names(db_name: str) -> List[str]:
    """
    Get table names for database type.

    Args:
        db_name: Database name (raw, total, log, ml)

    Returns:
        List of table names
    """
    tables = {
        'raw': ['sensor_data'],
        'total': ['processed_data', 'cutting_sessions'],
        'log': ['system_logs'],
        'ml': ['ml_predictions']
    }

    return tables.get(db_name, [])


def _compress_old_backups(daily_dir: Path, compress_after_days: int):
    """
    Compress backups older than threshold.

    Args:
        daily_dir: Daily backups directory
        compress_after_days: Compress backups older than this many days
    """
    try:
        threshold_date = datetime.now() - timedelta(days=compress_after_days)

        for backup_dir in daily_dir.iterdir():
            if not backup_dir.is_dir():
                continue

            try:
                # Parse date from folder name (YYYY-MM-DD)
                backup_date = datetime.strptime(backup_dir.name, '%Y-%m-%d')

                if backup_date < threshold_date:
                    # Compress all .db files in this folder
                    for db_file in backup_dir.glob('*.db'):
                        gz_file = db_file.with_suffix('.db.gz')

                        if not gz_file.exists():
                            logger.info(f"Compressing {db_file.name}...")

                            with open(db_file, 'rb') as f_in:
                                with gzip.open(gz_file, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)

                            # Delete original
                            db_file.unlink()

            except ValueError:
                # Invalid folder name, skip
                logger.warning(f"Invalid backup folder name: {backup_dir.name}")
                continue

    except Exception as e:
        logger.error(f"Error compressing old backups: {e}", exc_info=True)


def _delete_old_backups(daily_dir: Path, retention_days: int):
    """
    Delete backups older than retention period.

    Args:
        daily_dir: Daily backups directory
        retention_days: Keep backups for this many days
    """
    try:
        retention_date = datetime.now() - timedelta(days=retention_days)

        for backup_dir in daily_dir.iterdir():
            if not backup_dir.is_dir():
                continue

            try:
                # Parse date from folder name (YYYY-MM-DD)
                backup_date = datetime.strptime(backup_dir.name, '%Y-%m-%d')

                if backup_date < retention_date:
                    logger.info(f"Deleting old backup: {backup_dir.name}")
                    shutil.rmtree(backup_dir)

            except ValueError:
                # Invalid folder name, skip
                logger.warning(f"Invalid backup folder name: {backup_dir.name}")
                continue

    except Exception as e:
        logger.error(f"Error deleting old backups: {e}", exc_info=True)


def load_config(config_path: Path) -> dict:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config.yaml

    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    # CLI entry point for subprocess
    parser = argparse.ArgumentParser(description="Database backup task")
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to config.yaml"
    )

    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Perform backup
    perform_daily_backup(config)
