"""
Camera vision services.

This module will contain:
- CameraService: Frame capture (S20)
- CameraResultsStore: Thread-safe results store (S20)
- DetectionWorker: RT-DETR broken/crack detection (S21)
- LDCWorker: Edge detection wear measurement (S21)
- SawHealthCalculator: Health score calculation (S21)
- VisionService: Orchestration (S22)
"""

from src.services.camera.results_store import CameraResultsStore
from src.services.camera.camera_service import CameraService

__all__ = ["CameraResultsStore", "CameraService"]
