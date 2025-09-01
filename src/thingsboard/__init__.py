"""ThingsBoard entegrasyon modülü.

Bu paket, bir cihaz erişim belirteci (access token) kullanarak ThingsBoard
sunucusuna telemetri ve öznitelik (attributes) verilerini HTTP üzerinden
göndermek için basit bir istemci sağlar.
"""

from .sender import ThingsBoardSender, create_sender_from_env

__all__ = ["ThingsBoardSender", "create_sender_from_env"]


