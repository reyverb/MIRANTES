import csv
import io
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.operations import DownloadCreate, PieceCreate, ManifestRequest
from app.services.business import classify_weight, dashboard_summary, commercial_class, manifest

router = APIRouter(tags=["operations"])

@router.get("/descargas")
def list_downloads(status: str | None = Query(default=None, pattern=r"^(Em Andamento|Concluída)$"), db: Session = Depends(get_db)):
    sql = "SELECT d.id, d.barco, d.proprietario, d.datahora, d.status, COUNT(p.id) AS total_pecas, COALESCE(SUM(p.pesokg),0) AS total_kg FROM descargas d LEFT JOIN pecas p ON p.iddescarga=d.id"
    params = {}
    if status:
        sql += " WHERE d.status=:status"
        params["status"] = status
    sql += " GROUP BY d.id ORDER BY d.id DESC"
    rows = db.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]

@router.post("/descargas", status_code=201)
def create_download(data: DownloadCreate, db: Session = Depends(get_db)):
    row = db.execute(text("INSERT INTO descargas (barco, proprietario, datahora, status) VALUES (:boat,:owner,:now,'Em Andamento') RETURNING id, barco, proprietario, datahora, status"), {"boat": data.boat.strip(), "owner": data.owner.strip(), "now": datetime.now(timezone.utc)}).mappings().one()
    db.commit()
    return dict(row)

@router.get("/descargas/{download_id}")
def get_download(download_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT id, barco, proprietario, datahora, status FROM descargas WHERE id=:id"), {"id": download_id}).mappings().first()
    if not row: raise HTTPException(404, "Descarga não encontrada")
    return dict(row)

@router.patch("/descargas/{download_id}/concluir")
def close_download(download_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("UPDATE descargas SET status='Concluída' WHERE id=:id AND status='Em Andamento' RETURNING id,status"), {"id": download_id}).mappings().first()
    if not row: raise HTTPException(404, "Descarga ativa não encontrada")
    db.commit()
    return dict(row)

@router.get("/descargas/{download_id}/pecas")
def list_pieces(download_id: int, destination: str | None = None, db: Session = Depends(get_db)):
    sql = "SELECT id, iddescarga, numeropeca, pesokg, categoria, segundofuro, lombo, destino, dataregistro FROM pecas WHERE iddescarga=:id"
    params = {"id": download_id}
    if destination:
        sql += " AND destino=:destination"
        params["destination"] = destination
    sql += " ORDER BY numeropeca DESC"
    return [dict(r) for r in db.execute(text(sql), params).mappings().all()]

@router.post("/descargas/{download_id}/pecas", status_code=201)
def add_piece(download_id: int, data: PieceCreate, db: Session = Depends(get_db)):
    try:
        with db.begin():
            dl = db.execute(text("SELECT id FROM descargas WHERE id=:id AND status='Em Andamento' FOR UPDATE"), {"id": download_id}).first()
            if not dl: raise HTTPException(404, "Descarga ativa não encontrada")
            number = db.execute(text("SELECT COALESCE(MAX(numeropeca),0)+1 FROM pecas WHERE iddescarga=:id"), {"id": download_id}).scalar_one()
            row = db.execute(text("INSERT INTO pecas (iddescarga,numeropeca,pesokg,categoria,segundofuro,lombo,destino,dataregistro) VALUES (:download,:number,:weight,:category,:hole,:loin,:destination,:now) RETURNING id,iddescarga,numeropeca,pesokg,categoria,segundofuro,lombo,destino,dataregistro"), {"download":download_id,"number":number,"weight":data.weight_kg,"category":classify_weight(data.weight_kg),"hole":data.second_hole,"loin":data.loin,"destination":data.destination,"now":datetime.now(timezone.utc)}).mappings().one()
        return dict(row)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(409, "Conflito ao numerar peça; tente novamente") from error

@router.delete("/descargas/{download_id}/pecas/ultima")
def delete_latest_piece(download_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("DELETE FROM pecas WHERE id=(SELECT id FROM pecas WHERE iddescarga=:id ORDER BY id DESC LIMIT 1) RETURNING id,numeropeca"), {"id":download_id}).mappings().first()
    if not row: raise HTTPException(404, "Não há peças para remover")
    db.commit()
    return dict(row)

@router.get("/descargas/{download_id}/resumo")
def summary(download_id: int, db: Session = Depends(get_db)):
    dl = db.execute(text("SELECT id,barco,proprietario,datahora,status FROM descargas WHERE id=:id"), {"id":download_id}).mappings().first()
    if not dl: raise HTTPException(404, "Descarga não encontrada")
    pieces = [dict(r) for r in db.execute(text("SELECT pesokg AS weight_kg,segundofuro AS second_hole,lombo AS loin FROM pecas WHERE iddescarga=:id"), {"id":download_id}).mappings().all()]
    return {"download":dict(dl), **dashboard_summary(pieces)}

@router.get("/descargas/{download_id}/evolucao-pecas")
def piece_evolution(download_id: int, db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT numeropeca,pesokg,categoria,segundofuro,lombo,destino,dataregistro FROM pecas WHERE iddescarga=:id ORDER BY numeropeca"), {"id":download_id}).mappings().all()
    return [dict(r) for r in rows]

@router.get("/descargas/{download_id}/distribuicao-destino")
def destination_summary(download_id: int, db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT destino,COALESCE(SUM(pesokg),0) AS total_kg,COUNT(*) AS pieces FROM pecas WHERE iddescarga=:id GROUP BY destino ORDER BY destino"), {"id":download_id}).mappings().all()
    return [dict(r) for r in rows]

@router.get("/descargas/{download_id}/fechamento-categorias")
def category_summary(download_id: int, db: Session = Depends(get_db)):
    pieces = [dict(r) for r in db.execute(text("SELECT numeropeca,pesokg AS weight_kg,categoria,segundofuro AS second_hole,lombo AS loin FROM pecas WHERE iddescarga=:id"), {"id":download_id}).mappings().all()]
    groups = {}
    for p in pieces:
        category = commercial_class(p)
        item = groups.setdefault(category, {"categoria":category,"pecas":0,"peso_total_kg":0.0,"com_2_furo":0,"com_lombo":0})
        item["pecas"] += 1
        item["peso_total_kg"] += p["weight_kg"]
        item["com_2_furo"] += int(bool(p["second_hole"]))
        item["com_lombo"] += int(bool(p["loin"]))
    return list(groups.values())

@router.post("/descargas/{download_id}/romaneio")
def commercial_manifest(download_id: int, request: ManifestRequest, db: Session = Depends(get_db)):
    pieces = [dict(r) for r in db.execute(text("SELECT pesokg AS weight_kg,segundofuro AS second_hole,lombo AS loin FROM pecas WHERE iddescarga=:id"), {"id":download_id}).mappings().all()]
    return {"download_id":download_id, **manifest(pieces, request.prices.model_dump())}

@router.get("/descargas/{download_id}/export.csv")
def export_csv(download_id: int, db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT numeropeca,pesokg,categoria,segundofuro,lombo,destino,dataregistro FROM pecas WHERE iddescarga=:id ORDER BY numeropeca"), {"id":download_id}).mappings().all()
    if not rows: raise HTTPException(404, "Descarga sem peças")
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()), delimiter=";")
    writer.writeheader(); writer.writerows([dict(r) for r in rows])
    return StreamingResponse(iter(["\ufeff"+stream.getvalue()]), media_type="text/csv; charset=utf-8", headers={"Content-Disposition":f"attachment; filename=descarga_{download_id}.csv"})

@router.post("/descargas/{download_id}/relatorio.pdf")
def export_pdf(download_id: int, request: ManifestRequest, db: Session = Depends(get_db)):
    dl = db.execute(text("SELECT barco,proprietario,datahora FROM descargas WHERE id=:id"), {"id":download_id}).mappings().first()
    if not dl: raise HTTPException(404,"Descarga não encontrada")
    pieces = [dict(r) for r in db.execute(text("SELECT pesokg AS weight_kg,segundofuro AS second_hole,lombo AS loin FROM pecas WHERE iddescarga=:id"), {"id":download_id}).mappings().all()]
    summary_data = dashboard_summary(pieces); manifest_data = manifest(pieces, request.prices.model_dump())
    buffer=io.BytesIO(); pdf=canvas.Canvas(buffer,pagesize=A4); width,height=A4; y=height-50
    pdf.setFont("Helvetica-Bold",16); pdf.drawString(40,y,"NAVIMAR PESCADOS - Relatório de descarga"); y-=30
    pdf.setFont("Helvetica",10)
    for line in [f"Barco: {dl['barco']}",f"Proprietário: {dl['proprietario']}",f"Data: {dl['datahora']}",f"Peças: {summary_data['pieces']}",f"Peso total: {summary_data['total_kg']:.2f} kg",f"Média: {summary_data['average_kg']:.2f} kg",f"Valor estimado: R$ {manifest_data['total_value']:.2f}"]:
        pdf.drawString(40,y,line); y-=18
    y-=10; pdf.setFont("Helvetica-Bold",11); pdf.drawString(40,y,"Romaneio comercial"); y-=20
    pdf.setFont("Helvetica",9)
    for item in manifest_data["items"]:
        pdf.drawString(40,y,f"{item['category']}: {item['kg']:.2f} kg x R$ {item['price_per_kg']:.2f} = R$ {item['total']:.2f}"); y-=16
    pdf.save(); buffer.seek(0)
    return StreamingResponse(buffer,media_type="application/pdf",headers={"Content-Disposition":f"attachment; filename=romaneio_{download_id}.pdf"})
