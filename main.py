from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.middleware.cors import CORSMiddleware

# FastAPI apps
from booking_manager.main import app as booking_app
from dashboard.main import app as dashboard_app
from cancellations_panel.main import app as cancellations_app
from chat.app import app as chat_app

# Flask apps
from ai_settings.ai_settings import app as ai_settings_app
from admin_controls.admin_controls import app as admin_controls_app
from monitoring.monitoring import app as monitoring_app
from reports.reports import app as reports_app
from standby.app import app as standby_app

app = FastAPI(title="Unified Watsapp API", description="Combined API for all Watsapp services")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount FastAPI apps (ASGI)
app.mount("/booking", booking_app)
app.mount("/dashboard", dashboard_app)
app.mount("/cancellations", cancellations_app)
app.mount("/chat", chat_app)

# Mount Flask apps (WSGI)
app.mount("/ai", WSGIMiddleware(ai_settings_app))
app.mount("/admin", WSGIMiddleware(admin_controls_app))
app.mount("/monitoring", WSGIMiddleware(monitoring_app))
app.mount("/reports", WSGIMiddleware(reports_app))
app.mount("/standby", WSGIMiddleware(standby_app))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)