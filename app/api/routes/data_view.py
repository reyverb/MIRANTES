from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Visualização de Dados"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/dados", response_class=HTMLResponse)
async def pagina_visualizacao_dados(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="data_view.html",
        context={
            "titulo": "Visualização de Dados",
            "subtitulo": "Consulta e análise das descargas de atum",
        },
    )
