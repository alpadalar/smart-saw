import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# API modülünü import et
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api import create_app

# FastAPI uygulamasi olustur
app = create_app()

# Webui dizinini bul
current_dir = os.path.dirname(os.path.abspath(__file__))
webui_dir = os.path.join(current_dir, "webui")

# Statik dosyalari monte et
app.mount("/", StaticFiles(directory=webui_dir, html=True), name="webui")

# Ana sayfaya yonlendirme
@app.get("/")
async def redirect_to_index():
    return RedirectResponse(url="/index.html")

if __name__ == "__main__":
    print(f"Web arayuzu dosyalari: {webui_dir}")
    print("Web sunucusu baslatiliyor. http://localhost:8080 adresinden erisebilirsiniz...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
