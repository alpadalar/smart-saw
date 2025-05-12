import requests
import json
import websockets
import asyncio
from datetime import datetime
import sys
import os

# API temel URL'si
BASE_URL = "http://localhost:8080"

# Test sonuçlarını saklamak için sınıf
class TestResult:
    def __init__(self, endpoint, method, status_code, response_time, success, error=None):
        self.endpoint = endpoint
        self.method = method
        self.status_code = status_code
        self.response_time = response_time
        self.success = success
        self.error = error
        self.timestamp = datetime.now()

    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"{status} {self.method} {self.endpoint} - Status: {self.status_code} - Time: {self.response_time:.2f}s"

# Test sonuçlarını saklamak için liste
test_results = []

def print_test_results():
    print("\n=== Test Sonuçları ===")
    for result in test_results:
        print(result)
        if not result.success and result.error:
            print(f"   Hata: {result.error}")

async def test_websocket():
    """WebSocket bağlantısını test eder"""
    try:
        async with websockets.connect(f"ws://localhost:8080/logs/ws") as websocket:
            print("WebSocket bağlantısı başarılı")
            # 5 saniye boyunca mesajları dinle
            for _ in range(5):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    print(f"WebSocket mesajı alındı: {message[:100]}...")
                except asyncio.TimeoutError:
                    continue
    except Exception as e:
        print(f"WebSocket test hatası: {str(e)}")

def test_endpoint(endpoint, method="GET", data=None):
    """Belirtilen endpoint'i test eder"""
    url = f"{BASE_URL}{endpoint}"
    start_time = datetime.now()
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        else:
            raise ValueError(f"Desteklenmeyen HTTP metodu: {method}")
        
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Yanıtı kontrol et
        success = 200 <= response.status_code < 300
        error = None if success else response.text
        
        result = TestResult(
            endpoint=endpoint,
            method=method,
            status_code=response.status_code,
            response_time=response_time,
            success=success,
            error=error
        )
        
        test_results.append(result)
        return result
        
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds()
        result = TestResult(
            endpoint=endpoint,
            method=method,
            status_code=0,
            response_time=response_time,
            success=False,
            error=str(e)
        )
        test_results.append(result)
        return result

def run_tests():
    """Tüm API testlerini çalıştırır"""
    print("API testleri başlatılıyor...")
    
    # Sistem durumu testi
    print("\nSistem durumu testi yapılıyor...")
    test_endpoint("/status")
    
    # Gerçek zamanlı veri testi
    print("\nGerçek zamanlı veri testi yapılıyor...")
    test_endpoint("/data/realtime")
    
    # Log dosyaları testi
    print("\nLog dosyaları testi yapılıyor...")
    test_endpoint("/logs/files")
    
    # Log seviyeleri testi
    print("\nLog seviyeleri testi yapılıyor...")
    test_endpoint("/logs/levels")
    
    # Log kaynakları testi
    print("\nLog kaynakları testi yapılıyor...")
    test_endpoint("/logs/sources")
    
    # Örnek bir log dosyası testi (eğer varsa)
    print("\nLog dosyası okuma testi yapılıyor...")
    test_endpoint("/logs/app.log")
    
    # Log dosyası son satırları testi
    print("\nLog dosyası son satırları testi yapılıyor...")
    test_endpoint("/logs/app.log/tail?n=10")
    
    # Hız güncelleme testi
    print("\nHız güncelleme testi yapılıyor...")
    speed_data = {
        "cutting_speed": 10.0,
        "feed_speed": 5.0
    }
    test_endpoint("/control/speed", method="POST", data=speed_data)
    
    # Kontrol modu güncelleme testi
    print("\nKontrol modu güncelleme testi yapılıyor...")
    controller_data = {
        "mode": "manual"
    }
    test_endpoint("/control/mode", method="POST", data=controller_data)
    
    # Test sonuçlarını yazdır
    print_test_results()

async def main():
    """Ana test fonksiyonu"""
    # HTTP endpoint testleri
    run_tests()
    
    # WebSocket testi
    print("\nWebSocket testi yapılıyor...")
    await test_websocket()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTestler kullanıcı tarafından durduruldu.")
    except Exception as e:
        print(f"\nTestler sırasında hata oluştu: {str(e)}")
    finally:
        print("\nTestler tamamlandı.") 