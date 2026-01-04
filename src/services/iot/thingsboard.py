"""
ThingsBoard data formatting and telemetry preparation.
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ThingsBoardFormatter:
    """
    Format data for ThingsBoard telemetry API.

    ThingsBoard expects JSON payload:
    {
        "ts": <timestamp_milliseconds>,
        "values": {
            "field1": value1,
            "field2": value2,
            ...
        }
    }
    """

    def __init__(self, config: dict):
        """
        Initialize formatter.

        Args:
            config: IoT configuration with telemetry field mapping
        """
        self.config = config

        # Fields to include in telemetry
        self.telemetry_fields = config.get('thingsboard', {}).get(
            'telemetry_fields',
            []
        )

        logger.info(
            f"ThingsBoardFormatter initialized: "
            f"{len(self.telemetry_fields)} telemetry fields"
        )

    def format_telemetry(self, processed_data) -> Dict[str, Any]:
        """
        Format ProcessedData for ThingsBoard telemetry.

        Args:
            processed_data: ProcessedData instance

        Returns:
            Dictionary with ThingsBoard telemetry format
        """
        try:
            raw_data = processed_data.raw_data

            # Build values dictionary
            values = {}

            # Map configured fields from raw_data
            field_mapping = {
                'serit_motor_akim_a': raw_data.serit_motor_akim_a,
                'serit_motor_tork_percentage': raw_data.serit_motor_tork_percentage,
                'inme_motor_akim_a': raw_data.inme_motor_akim_a,
                'inme_motor_tork_percentage': raw_data.inme_motor_tork_percentage,
                'serit_kesme_hizi': raw_data.serit_kesme_hizi,
                'serit_inme_hizi': raw_data.serit_inme_hizi,
                'kafa_yuksekligi_mm': raw_data.kafa_yuksekligi_mm,
                'serit_sapmasi': raw_data.serit_sapmasi,
                'serit_gerginligi_bar': raw_data.serit_gerginligi_bar,
                'mengene_basinc_bar': raw_data.mengene_basinc_bar,
                'ortam_sicakligi_c': raw_data.ortam_sicakligi_c,
                'ortam_nem_percentage': raw_data.ortam_nem_percentage,
                'sogutma_sivi_sicakligi_c': raw_data.sogutma_sivi_sicakligi_c,
                'hidrolik_yag_sicakligi_c': raw_data.hidrolik_yag_sicakligi_c,
                'ivme_olcer_x': raw_data.ivme_olcer_x,
                'ivme_olcer_y': raw_data.ivme_olcer_y,
                'ivme_olcer_z': raw_data.ivme_olcer_z,
                'ivme_olcer_x_hz': raw_data.ivme_olcer_x_hz,
                'ivme_olcer_y_hz': raw_data.ivme_olcer_y_hz,
                'ivme_olcer_z_hz': raw_data.ivme_olcer_z_hz,
                'max_titresim_hz': raw_data.max_titresim_hz,
                'testere_durumu': raw_data.testere_durumu,
                'alarm_status': raw_data.alarm_status,
                'makine_id': raw_data.makine_id,
                'serit_id': raw_data.serit_id
            }

            # Add processed data fields
            field_mapping.update({
                'ml_output': processed_data.ml_output,
                'torque_guard_active': int(processed_data.torque_guard_active),
                'is_cutting': int(processed_data.is_cutting),
                'controller_type': processed_data.controller_type,
                'cutting_session_id': processed_data.cutting_session_id,
                'anomaly_count': len(processed_data.anomalies) if processed_data.anomalies else 0
            })

            # Filter to configured fields (or all if not configured)
            if self.telemetry_fields:
                for field in self.telemetry_fields:
                    if field in field_mapping and field_mapping[field] is not None:
                        values[field] = field_mapping[field]
            else:
                # Include all non-None values
                values = {
                    k: v for k, v in field_mapping.items()
                    if v is not None
                }

            # Convert timestamp to milliseconds
            timestamp_ms = int(processed_data.timestamp.timestamp() * 1000)

            # ThingsBoard format
            telemetry = {
                "ts": timestamp_ms,
                "values": values
            }

            return telemetry

        except Exception as e:
            logger.error(f"Error formatting telemetry: {e}", exc_info=True)
            return {}

    def format_attributes(self, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format device attributes for ThingsBoard.

        Attributes are static/semi-static device properties.

        Args:
            device_info: Dictionary with device information

        Returns:
            Dictionary with ThingsBoard attributes format
        """
        try:
            return {
                "model": device_info.get("model", "Smart Band Saw"),
                "version": device_info.get("version", "1.0.0"),
                "location": device_info.get("location", "Unknown"),
                "installation_date": device_info.get("installation_date", ""),
                "serial_number": device_info.get("serial_number", "")
            }

        except Exception as e:
            logger.error(f"Error formatting attributes: {e}", exc_info=True)
            return {}
