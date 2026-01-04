"""
Backup service - schedules daily database backups in separate process.
"""

import asyncio
import logging
import subprocess
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class BackupService:
    """
    Automated daily backup scheduler.

    Features:
    - Runs backup in separate process (avoids file locks)
    - Daily scheduling at configured time (default: 03:00)
    - Manual trigger support
    - Error handling and logging
    """

    def __init__(self, config: dict):
        """
        Initialize backup service.

        Args:
            config: System configuration dictionary
        """
        self.config = config

        # Backup configuration
        backup_config = config.get('backup', {})
        self.enabled = backup_config.get('enabled', True)
        self.backup_time = self._parse_time(
            backup_config.get('time', '03:00')
        )

        # Paths
        self.config_path = Path(config.get('config_path', 'config/config.yaml'))
        self.backup_script = Path(__file__).parent.parent.parent / 'tasks' / 'backup.py'

        # State
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._last_backup_time: Optional[datetime] = None

        logger.info(
            f"BackupService initialized: "
            f"enabled={self.enabled}, "
            f"time={self.backup_time.strftime('%H:%M')}"
        )

    def _parse_time(self, time_str: str) -> time:
        """
        Parse time string (HH:MM format).

        Args:
            time_str: Time string (e.g., "03:00")

        Returns:
            datetime.time object
        """
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour=hour, minute=minute)
        except Exception as e:
            logger.error(f"Invalid backup time format: {time_str}, using 03:00")
            return time(hour=3, minute=0)

    async def start(self):
        """
        Start backup scheduler.
        """
        if not self.enabled:
            logger.info("Backup service disabled")
            return

        if self._running:
            logger.warning("Backup service already running")
            return

        self._running = True

        # Start scheduler task
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())

        logger.info("Backup scheduler started")

    async def stop(self, timeout: float = 5.0):
        """
        Stop backup scheduler.

        Args:
            timeout: Maximum time to wait for scheduler
        """
        if not self._running:
            return

        self._running = False

        # Cancel scheduler task
        if self._scheduler_task:
            self._scheduler_task.cancel()

            try:
                await asyncio.wait_for(self._scheduler_task, timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("Backup scheduler stop timeout")

        logger.info("Backup scheduler stopped")

    async def _scheduler_loop(self):
        """
        Scheduler loop - triggers backup at configured time.
        """
        logger.info("Backup scheduler loop started")

        while self._running:
            try:
                # Calculate next backup time
                now = datetime.now()
                next_backup = self._calculate_next_backup_time(now)

                # Wait until next backup time
                wait_seconds = (next_backup - now).total_seconds()

                logger.info(
                    f"Next backup scheduled at: "
                    f"{next_backup.strftime('%Y-%m-%d %H:%M')}"
                )

                await asyncio.sleep(wait_seconds)

                # Trigger backup
                if self._running:
                    await self.trigger_backup()

            except asyncio.CancelledError:
                logger.info("Backup scheduler cancelled")
                break

            except Exception as e:
                logger.error(f"Error in backup scheduler: {e}", exc_info=True)
                # Wait 1 hour before retry
                await asyncio.sleep(3600)

        logger.info("Backup scheduler loop ended")

    def _calculate_next_backup_time(self, now: datetime) -> datetime:
        """
        Calculate next backup time.

        Args:
            now: Current datetime

        Returns:
            Next backup datetime
        """
        # Today's backup time
        next_backup = datetime.combine(now.date(), self.backup_time)

        # If already passed today, use tomorrow
        if next_backup <= now:
            next_backup += timedelta(days=1)

        return next_backup

    async def trigger_backup(self) -> bool:
        """
        Trigger backup manually (runs in subprocess).

        Returns:
            True if backup successful, False otherwise
        """
        try:
            logger.info("=" * 60)
            logger.info("Triggering database backup...")
            logger.info("=" * 60)

            # Build command
            cmd = [
                sys.executable,  # Python interpreter
                str(self.backup_script),
                '--config', str(self.config_path)
            ]

            # Run backup in subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for completion
            stdout, stderr = await process.communicate()

            # Log output
            if stdout:
                logger.info("Backup output:\n" + stdout.decode())

            if stderr:
                logger.error("Backup errors:\n" + stderr.decode())

            # Check return code
            if process.returncode == 0:
                self._last_backup_time = datetime.now()
                logger.info("Backup completed successfully")
                return True
            else:
                logger.error(f"Backup failed with code: {process.returncode}")
                return False

        except Exception as e:
            logger.error(f"Error triggering backup: {e}", exc_info=True)
            return False

    def get_status(self) -> dict:
        """
        Get backup service status.

        Returns:
            Dictionary with status information
        """
        return {
            'enabled': self.enabled,
            'running': self._running,
            'backup_time': self.backup_time.strftime('%H:%M'),
            'last_backup': (
                self._last_backup_time.isoformat()
                if self._last_backup_time else None
            )
        }
