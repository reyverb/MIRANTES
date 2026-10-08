from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes.health import router as health_router
from app.api.routes.operations import router as operations_router
from app.api.routes.data_view import router as data_view_router
from app.api.routes.reports import router as reports_router
from app.core.config import settings

app = FastAPI(title="NAVIMAR PESCADOS", version="2.0.0", description="Operação de descargas e dashboard")
origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=bool(origins), allow_methods=["*"], allow_headers=["Authorization", "Content-Type"])
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
app.include_router(health_router)
app.include_router(operations_router, prefix="/api/v1")
app.include_router(data_view_router)
app.include_router(reports_router)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})
