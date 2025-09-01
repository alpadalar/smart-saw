import time
import serial

def get_crc(data):
    """CRC hesaplama"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc = crc >> 1
    return crc

def write_register(serial, reg_addr, value):
    """Register'a yazma yap"""
    command = [
        0x50,           # Cihaz adresi
        0x06,           # Fonksiyon kodu (06: yazma)
        reg_addr >> 8,  # Register adresi (yüksek byte)
        reg_addr & 0xFF,# Register adresi (düşük byte)
        value >> 8,     # Değer (yüksek byte)
        value & 0xFF    # Değer (düşük byte)
    ]
    
    # CRC ekle
    crc = get_crc(command)
    command.append(crc & 0xFF)
    command.append(crc >> 8)
    
    # Komutu gönder
    serial.write(bytes(command))
    print(f"Register yazma komutu gönderildi (0x{reg_addr:04X} -> 0x{value:04X}): {[hex(x) for x in command]}")
    
    # Yanıtı bekle
    response = serial.read(8)
    
    if len(response) == 8:
        # CRC kontrolü
        received_crc = response[-2] | (response[-1] << 8)
        calculated_crc = get_crc(response[:-2])
        
        if received_crc == calculated_crc:
            print("Register yazma başarılı:", [hex(x) for x in response])
            return True
        else:
            print("CRC hatası:", [hex(x) for x in response])
    else:
        print(f"Geçersiz yanıt uzunluğu: {len(response)}", [hex(x) for x in response])
    return False

def set_highspeed_mode(port='COM6'):
    try:
        # Seri port bağlantısı
        ser = serial.Serial(
            port=port,
            baudrate=9600,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=0.5
        )
        print(f"Seri port bağlantısı kuruldu: {port} (9600 baud)")
        
        # Kilidi açmak için sabit komut
        unlock_command = [0x50, 0x06, 0x00, 0x69, 0xB5, 0x88]
        # CRC ekle
        crc = get_crc(unlock_command)
        unlock_command.append(crc & 0xFF)
        unlock_command.append(crc >> 8)
        
        ser.write(bytes(unlock_command))
        print("Kilit açma komutu gönderildi:", [hex(x) for x in unlock_command])
        time.sleep(0.5)
        
        # Yanıtı kontrol et
        response = ser.read(8)
        if len(response) == 8:
            print("Kilit açma yanıtı alındı:", [hex(x) for x in response])
            if all(x == 0 for x in response):
                print("UYARI: Kilit açma yanıtı boş geldi! Tekrar deneniyor...")
                time.sleep(0.5)
                ser.write(bytes(unlock_command))
                response = ser.read(8)
                if all(x == 0 for x in response):
                    print("HATA: İkinci denemede de kilit açılamadı!")
                    ser.close()
                    return False
        
        # Yüksek hız modunu aktif et
        if write_register(ser, 0x62, 0x0001):
            time.sleep(0.5)
            # Değişiklikleri kaydet
            save_command = [0x50, 0x06, 0x00, 0x00, 0x00, 0x84]
            # CRC ekle
            crc = get_crc(save_command)
            save_command.append(crc & 0xFF)
            save_command.append(crc >> 8)
            
            ser.write(bytes(save_command))
            print("Save komutu gönderildi:", [hex(x) for x in save_command])
            time.sleep(0.5)
            
            # Save yanıtını kontrol et
            response = ser.read(8)
            if len(response) == 8:
                print("Save yanıtı alındı:", [hex(x) for x in response])
                if all(x == 0 for x in response):
                    print("UYARI: Save yanıtı boş geldi! Tekrar deneniyor...")
                    time.sleep(0.5)
                    ser.write(bytes(save_command))
                    response = ser.read(8)
                    if all(x == 0 for x in response):
                        print("HATA: İkinci denemede de save yapılamadı!")
                        ser.close()
                        return False
            
            print("Yüksek hız modu başarıyla aktifleştirildi!")
            print("Cihazı 230400 baud rate ile kullanabilirsiniz.")
            ser.close()
            return True
        else:
            print("HATA: Register yazma başarısız!")
            ser.close()
            return False
            
    except Exception as e:
        print(f"HATA: {str(e)}")
        if 'ser' in locals():
            ser.close()
        return False

if __name__ == "__main__":
    import sys
    
    # Port argümanı varsa kullan, yoksa COM7'yi kullan
    port = sys.argv[1] if len(sys.argv) > 1 else 'COM6'
    
    print("Yüksek hız modu ayarlanıyor...")
    if set_highspeed_mode(port):
        print("İşlem başarılı!")
    else:
        print("İşlem başarısız!") 