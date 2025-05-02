# src/api/routes.py
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, Depends
from typing import Dict, List, Optional, Set
from datetime import datetime

from core.logger import logger
from core.constants import ControllerType, SPEED_LIMITS, TestereState
from control.factory import get_controller_factory
from utils.helpers import validate_speed_limits, reverse_calculate_value
from hardware.modbus.client import ModbusClient
from data.cutting_tracker import get_cutting_tracker
from .api_models import (
    SystemStatus,
    SpeedUpdate,
    ControllerUpdate,
    MachineData,
    DetailedMachineData,
    RealtimeData,
    CuttingInfo,
    APIResponse,
    WebSocketMessage,
    LogEntry,
    LogFilter
)
from .websocket import WebSocketManager
from .log_reader import get_log_reader

router = APIRouter(prefix="/api/v1")
controller_factory = get_controller_factory()
ws_manager = WebSocketManager()
cutting_tracker = get_cutting_tracker()
log_reader = get_log_reader()

@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Sistem durumunu döndürür"""
    try:
        modbus = ModbusClient()
        current_data = modbus.read_all() if modbus.is_connected else None
        active_controller = controller_factory.active_controller

        return SystemStatus(
            status="running",
            active_controller=active_controller.value if active_controller else None,
            modbus_connected=modbus.is_connected,
            last_update=datetime.now(),
            error_count=sum(stats["errors"] for stats in controller_factory.get_stats().values()),
            speeds={
                "cutting": current_data.get("serit_kesme_hizi", 0) if current_data else 0,
                "feed": current_data.get("serit_inme_hizi", 0) if current_data else 0
            },
            sensor_data={
                "current": current_data.get("serit_motor_akim_a", 0) if current_data else 0,
                "deviation": current_data.get("serit_sapmasi", 0) if current_data else 0,
                "height": current_data.get("kafa_yuksekligi_mm", 0) if current_data else 0
            }
        )
    except Exception as e:
        logger.error(f"Status API hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/realtime", response_model=RealtimeData)
async def get_realtime_data():
    """Gerçek zamanlı sensör verilerini döndürür"""
    try:
        modbus = ModbusClient()
        current_data = modbus.read_all() if modbus.is_connected else {}
        
        if not current_data:
            raise HTTPException(status_code=503, detail="Modbus verisi alınamadı")
        
        active_controller = controller_factory.active_controller
        cutting_info = cutting_tracker.get_cutting_info()
        
        return RealtimeData(
            timestamp=datetime.now(),
            testere_durumu=current_data.get("testere_durumu", 0),
            serit_motor_akim_a=current_data.get("serit_motor_akim_a", 0),
            serit_sapmasi=current_data.get("serit_sapmasi", 0),
            kafa_yuksekligi_mm=current_data.get("kafa_yuksekligi_mm", 0),
            serit_kesme_hizi=current_data.get("serit_kesme_hizi", 0),
            serit_inme_hizi=current_data.get("serit_inme_hizi", 0),
            controller_output=current_data.get("fuzzy_output", None),
            is_cutting=cutting_info["cutting_active"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Realtime veri alma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/detailed", response_model=DetailedMachineData)
async def get_detailed_data():
    """Detaylı makine verilerini döndürür"""
    try:
        modbus = ModbusClient()
        current_data = modbus.read_all() if modbus.is_connected else {}
        
        if not current_data:
            raise HTTPException(status_code=503, detail="Modbus verisi alınamadı")
            
        active_controller = controller_factory.active_controller
        
        # Tüm alanları doldur
        data = {
            "timestamp": datetime.now(),
            "serit_motor_akim_a": current_data.get("serit_motor_akim_a", 0),
            "serit_motor_tork_percentage": current_data.get("serit_motor_tork_percentage", 0),
            "inme_motor_akim_a": current_data.get("inme_motor_akim_a", 0),
            "inme_motor_tork_percentage": current_data.get("inme_motor_tork_percentage", 0),
            "serit_sapmasi": current_data.get("serit_sapmasi", 0),
            "kafa_yuksekligi_mm": current_data.get("kafa_yuksekligi_mm", 0),
            "testere_durumu": current_data.get("testere_durumu", 0),
            "serit_kesme_hizi": current_data.get("serit_kesme_hizi", 0),
            "serit_inme_hizi": current_data.get("serit_inme_hizi", 0),
            "controller_output": current_data.get("fuzzy_output", None),
            "fuzzy_output": current_data.get("fuzzy_output", None),
            "kesme_hizi_degisim": current_data.get("kesme_hizi_degisim", None),
            "ivme_olcer_x": current_data.get("ivme_olcer_x", None),
            "ivme_olcer_y": current_data.get("ivme_olcer_y", None),
            "ivme_olcer_z": current_data.get("ivme_olcer_z", None), 
            "ivme_olcer_x_hz": current_data.get("ivme_olcer_x_hz", None),
            "ivme_olcer_y_hz": current_data.get("ivme_olcer_y_hz", None),
            "ivme_olcer_z_hz": current_data.get("ivme_olcer_z_hz", None),
            "ortam_sicakligi_c": current_data.get("ortam_sicakligi_c", None),
            "ortam_nem_percentage": current_data.get("ortam_nem_percentage", None),
            "sogutma_sivi_sicakligi_c": current_data.get("sogutma_sivi_sicakligi_c", None),
            "hidrolik_yag_sicakligi_c": current_data.get("hidrolik_yag_sicakligi_c", None),
            "mengene_basinc_bar": current_data.get("mengene_basinc_bar", None),
            "serit_gerginligi_bar": current_data.get("serit_gerginligi_bar", None),
            "modbus_connected": modbus.is_connected,
            "active_controller": active_controller.value if active_controller else None
        }
        
        return DetailedMachineData(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detaylı veri alma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cutting/info", response_model=CuttingInfo)
async def get_cutting_info():
    """Son kesim bilgilerini döndürür"""
    try:
        info = cutting_tracker.get_cutting_info()
        
        return CuttingInfo(
            cutting_active=info['cutting_active'],
            last_cutting_start=info['last_cutting_start'],
            last_cutting_end=info['last_cutting_end'],
            last_cutting_duration_ms=info['last_cutting_duration_ms'],
            last_cutting_duration_formatted=info['last_cutting_duration_formatted'],
            cutting_count=info['cutting_count'],
            active_controller=info['active_controller']
        )
    except Exception as e:
        logger.error(f"Kesim bilgisi alma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cutting/history")
async def get_cutting_history(limit: int = 10):
    """Son kesim geçmişini döndürür"""
    try:
        history = cutting_tracker.get_cutting_history(limit)
        return {"history": history}
    except Exception as e:
        logger.error(f"Kesim geçmişi alma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/control/mode", response_model=APIResponse)
async def update_control_mode(update: ControllerUpdate):
    """Kontrol modunu değiştirir"""
    try:
        controller_type = ControllerType[update.mode.upper()]
        controller_factory.set_controller(controller_type)
        
        # WebSocket üzerinden bildirim gönder
        await ws_manager.broadcast(WebSocketMessage(
            type="controller_change",
            data={"mode": controller_type.value}
        ).dict())
        
        return APIResponse(
            status="success",
            message=f"Kontrol modu {controller_type.value} olarak değiştirildi",
            data={"mode": controller_type.value}
        )
    except Exception as e:
        logger.error(f"Kontrol modu değiştirme hatası: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/control/speed", response_model=APIResponse)
async def update_speeds(update: SpeedUpdate):
    """Kesme ve inme hızlarını günceller"""
    try:
        modbus = ModbusClient()
        if not modbus.is_connected:
            raise HTTPException(status_code=503, detail="Modbus bağlantısı yok")

        # Hızları güncelle
        kesme_hizi = validate_speed_limits(update.cutting_speed, 'kesme')
        inme_hizi = validate_speed_limits(update.feed_speed, 'inme')
        
        reverse_calculate_value(modbus, kesme_hizi, 'serit_kesme_hizi', False)
        reverse_calculate_value(modbus, inme_hizi, 'serit_inme_hizi', False)
        
        # WebSocket üzerinden bildirim gönder
        await ws_manager.broadcast(WebSocketMessage(
            type="speed_update",
            data={
                "cutting_speed": kesme_hizi,
                "feed_speed": inme_hizi
            }
        ).dict())
        
        return APIResponse(
            status="success",
            message="Hızlar güncellendi",
            data={
                "cutting_speed": kesme_hizi,
                "feed_speed": inme_hizi
            }
        )
    except Exception as e:
        logger.error(f"Hız güncelleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/control/stop", response_model=APIResponse)
async def emergency_stop():
    """Acil duruş yapar"""
    try:
        modbus = ModbusClient()
        if not modbus.is_connected:
            raise HTTPException(status_code=503, detail="Modbus bağlantısı yok")

        # Hızları sıfırla
        reverse_calculate_value(modbus, 0, 'serit_kesme_hizi', False)
        reverse_calculate_value(modbus, 0, 'serit_inme_hizi', False)
        
        # Kontrol sistemini devre dışı bırak
        controller_factory.set_controller(None)
        
        # WebSocket üzerinden bildirim gönder
        await ws_manager.broadcast(WebSocketMessage(
            type="emergency_stop",
            data={"timestamp": datetime.now().isoformat()}
        ).dict())
        
        return APIResponse(
            status="success",
            message="Acil duruş yapıldı",
            data=None
        )
    except Exception as e:
        logger.error(f"Acil duruş hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/files", response_model=List[str])
async def get_log_files():
    """Mevcut log dosyalarını listeler"""
    try:
        files = log_reader.get_available_log_files()
        return files
    except Exception as e:
        logger.error(f"Log dosyalarını listeleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/levels", response_model=List[str])
async def get_log_levels():
    """Mevcut log seviyelerini listeler"""
    try:
        levels = log_reader.get_available_log_levels()
        return list(levels)
    except Exception as e:
        logger.error(f"Log seviyelerini listeleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/sources", response_model=List[str])
async def get_log_sources():
    """Mevcut kaynak dosyaları listeler"""
    try:
        sources = log_reader.get_available_source_files()
        return list(sources)
    except Exception as e:
        logger.error(f"Kaynak dosyaları listeleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/{file_name}", response_model=List[LogEntry])
async def get_log_entries(
    file_name: str, 
    level: Optional[str] = None,
    search: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000)
):
    """Belirli bir log dosyasından kayıtları getirir"""
    try:
        # Dosya adının güvenli olduğundan emin ol
        if not file_name.endswith('.log') or '/' in file_name or '\\' in file_name:
            raise HTTPException(status_code=400, detail="Geçersiz log dosyası adı")
        
        filter_options = LogFilter(
            level=level,
            search_term=search,
            source_file=source,
            limit=limit
        )
        
        entries = log_reader.read_log_file(file_name, filter_options)
        return entries
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Log kayıtlarını getirme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/{file_name}/tail", response_model=List[LogEntry])
async def tail_log_file(file_name: str, n: int = Query(default=100, ge=1, le=1000)):
    """Belirli bir log dosyasının son n satırını getirir"""
    try:
        # Dosya adının güvenli olduğundan emin ol
        if not file_name.endswith('.log') or '/' in file_name or '\\' in file_name:
            raise HTTPException(status_code=400, detail="Geçersiz log dosyası adı")
        
        entries = log_reader.tail_log_file(file_name, n)
        return entries
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Log dosyasının son satırlarını getirme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/logs/ws")
async def log_websocket(websocket: WebSocket):
    """Log kayıtları için WebSocket bağlantısı"""
    await websocket.accept()
    try:
        # İlk olarak mevcut dosyaları ve yapılandırmaları gönder
        await websocket.send_json({
            "type": "config",
            "data": {
                "files": log_reader.get_available_log_files(),
                "levels": list(log_reader.get_available_log_levels()),
                "sources": list(log_reader.get_available_source_files())
            }
        })
        
        # İstemciden gelen komutları işle
        while True:
            data = await websocket.receive_json()
            command = data.get("command")
            
            if command == "subscribe":
                file_name = data.get("file_name", "smart_saw.log")
                level = data.get("level")
                search = data.get("search")
                source = data.get("source")
                limit = data.get("limit", 100)
                
                # Dosya adının güvenli olduğundan emin ol
                if not file_name.endswith('.log') or '/' in file_name or '\\' in file_name:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": "Geçersiz log dosyası adı"}
                    })
                    continue
                
                # İlk olarak son kayıtları gönder
                filter_options = LogFilter(
                    level=level,
                    search_term=search,
                    source_file=source,
                    limit=limit
                )
                entries = log_reader.read_log_file(file_name, filter_options)
                
                # Kayıtları JSON olarak dönüştür
                entries_json = []
                for entry in entries:
                    entries_json.append({
                        "timestamp": entry.timestamp.isoformat(),
                        "level": entry.level,
                        "message": entry.message,
                        "source": entry.source,
                        "line_number": entry.line_number
                    })
                
                await websocket.send_json({
                    "type": "initial_logs",
                    "data": {"entries": entries_json}
                })
            
            elif command == "tail":
                file_name = data.get("file_name", "smart_saw.log")
                n = data.get("n", 100)
                
                # Dosya adının güvenli olduğundan emin ol
                if not file_name.endswith('.log') or '/' in file_name or '\\' in file_name:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": "Geçersiz log dosyası adı"}
                    })
                    continue
                
                # Son kayıtları getir ve gönder
                entries = log_reader.tail_log_file(file_name, n)
                
                # Kayıtları JSON olarak dönüştür
                entries_json = []
                for entry in entries:
                    entries_json.append({
                        "timestamp": entry.timestamp.isoformat(),
                        "level": entry.level,
                        "message": entry.message,
                        "source": entry.source,
                        "line_number": entry.line_number
                    })
                
                await websocket.send_json({
                    "type": "log_tail",
                    "data": {"entries": entries_json}
                })
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Bilinmeyen komut"}
                })
    
    except WebSocketDisconnect:
        logger.info("Log WebSocket bağlantısı kapatıldı")
    except Exception as e:
        logger.error(f"Log WebSocket hatası: {str(e)}")
        await websocket.close()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket bağlantı noktası"""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # İstemciden gelen mesajları işle
            await ws_manager.broadcast(data)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)