import csv
import io
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.operations import DownloadCreate, PieceCreate, ManifestRequest
from app.services.business import classify_weight, dashboard_summary, commercial_class, manifest

router = APIRouter(tags=["operations"])

@router.get("/descargas")
def list_downloads(status: str | None = Query(default=None, pattern=r"^(Em Andamento|Concluída)$"), db: Session = Depends(get_db)):
    sql = "SELECT d.id,d.barco,d.proprietario,d.data_hora,d.status,COUNT(p.id) AS total_pecas,COALESCE(SUM(p.peso_kg),0) AS total_kg FROM descargas d LEFT JOIN pecas p ON p.id_descarga=d.id"
    params = {}
    if status:
        sql += " WHERE d.status=:status"
        params["status"] = status
    sql += " GROUP BY d.id ORDER BY d.id DESC"
    return [dict(r) for r in db.execute(text(sql), params).mappings().all()]

@router.post("/descargas", status_code=201)
def create_download(data: DownloadCreate, db: Session = Depends(get_db)):
    row = db.execute(text("INSERT INTO descargas (barco,proprietario,data_hora,status) VALUES (:boat,:owner,:now,'Em Andamento') RETURNING id,barco,proprietario,data_hora,status"), {"boat":data.boat.strip(),"owner":data.owner.strip(),"now":datetime.now(timezone.utc)}).mappings().one()
    db.commit()
    return dict(row)

@router.get("/descargas/{download_id}")
def get_download(download_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT id,barco,proprietario,data_hora,status FROM descargas WHERE id=:id"), {"id":download_id}).mappings().first()
    if not row: raise HTTPException(404,"Descarga não encontrada")
    return dict(row)

@router.patch("/descargas/{download_id}/concluir")
def close_download(download_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("UPDATE descargas SET status='Concluída' WHERE id=:id AND status='Em Andamento' RETURNING id,status"), {"id":download_id}).mappings().first()
    if not row: raise HTTPException(404,"Descarga ativa não encontrada")
    db.commit()
    return dict(row)

@router.get("/descargas/{download_id}/pecas")
def list_pieces(download_id: int, destination: str | None = None, db: Session = Depends(get_db)):
    sql = "SELECT id,id_descarga,numero_peca,peso_kg,categoria,segundo_furo,lombo,destino,data_registro FROM pecas WHERE id_descarga=:id"
    params={"id":download_id}
    if destination:
        sql += " AND destino=:destination"; params["destination"]=destination
    sql += " ORDER BY numero_peca DESC"
    return [dict(r) for r in db.execute(text(sql),params).mappings().all()]

@router.post("/descargas/{download_id}/pecas", status_code=201)
def add_piece(download_id: int, data: PieceCreate, db: Session = Depends(get_db)):
    try:
        with db.begin():
            dl=db.execute(text("SELECT id FROM descargas WHERE id=:id AND status='Em Andamento' FOR UPDATE"),{"id":download_id}).first()
            if not dl: raise HTTPException(404,"Descarga ativa não encontrada")
            number=db.execute(text("SELECT COALESCE(MAX(numero_peca),0)+1 FROM pecas WHERE id_descarga=:id"),{"id":download_id}).scalar_one()
            row=db.execute(text("INSERT INTO pecas (id_descarga,numero_peca,peso_kg,categoria,segundo_furo,lombo,destino,data_registro) VALUES (:download,:number,:weight,:category,:hole,:loin,:destination,:now) RETURNING id,id_descarga,numero_peca,peso_kg,categoria,segundo_furo,lombo,destino,data_registro"),{"download":download_id,"number":number,"weight":data.weight_kg,"category":classify_weight(data.weight_kg),"hole":data.second_hole,"loin":data.loin,"destination":data.destination,"now":datetime.now(timezone.utc)}).mappings().one()
        return dict(row)
    except IntegrityError as error:
        db.rollback(); raise HTTPException(409,"Conflito ao numerar peça; tente novamente") from error

@router.delete("/descargas/{download_id}/pecas/ultima")
def delete_latest_piece(download_id: int, db: Session = Depends(get_db)):
    row=db.execute(text("DELETE FROM pecas WHERE id=(SELECT id FROM pecas WHERE id_descarga=:id ORDER BY id DESC LIMIT 1) RETURNING id,numero_peca"),{"id":download_id}).mappings().first()
    if not row: raise HTTPException(404,"Não há peças para remover")
    db.commit(); return dict(row)

@router.get("/descargas/{download_id}/resumo")
def summary(download_id: int, db: Session = Depends(get_db)):
    dl=db.execute(text("SELECT id,barco,proprietario,data_hora,status FROM descargas WHERE id=:id"),{"id":download_id}).mappings().first()
    if not dl: raise HTTPException(404,"Descarga não encontrada")
    pieces=[dict(r) for r in db.execute(text("SELECT peso_kg AS weight_kg,segundo_furo AS second_hole,lombo AS loin FROM pecas WHERE id_descarga=:id"),{"id":download_id}).mappings().all()]
    return {"download":dict(dl),**dashboard_summary(pieces)}

@router.get("/descargas/{download_id}/evolucao-pecas")
def piece_evolution(download_id: int, db: Session = Depends(get_db)):
    return [dict(r) for r in db.execute(text("SELECT numero_peca,peso_kg,categoria,segundo_furo,lombo,destino,data_registro FROM pecas WHERE id_descarga=:id ORDER BY numero_peca"),{"id":download_id}).mappings().all()]

@router.get("/descargas/{download_id}/distribuicao-destino")
def destination_summary(download_id: int, db: Session = Depends(get_db)):
    return [dict(r) for r in db.execute(text("SELECT destino,COALESCE(SUM(peso_kg),0) AS total_kg,COUNT(*) AS pieces FROM pecas WHERE id_descarga=:id GROUP BY destino ORDER BY destino"),{"id":download_id}).mappings().all()]

@router.get("/descargas/{download_id}/fechamento-categorias")
def category_summary(download_id: int, db: Session = Depends(get_db)):
    pieces=[dict(r) for r in db.execute(text("SELECT numero_peca,peso_kg AS weight_kg,categoria,segundo_furo AS second_hole,lombo AS loin FROM pecas WHERE id_descarga=:id"),{"id":download_id}).mappings().all()]
    groups={}
    for p in pieces:
        category=commercial_class(p); item=groups.setdefault(category,{"categoria":category,"pecas":0,"peso_total_kg":0.0,"com_2_furo":0,"com_lombo":0})
        item["pecas"]+=1; item["peso_total_kg"]+=float(p["weight_kg"]); item["com_2_furo"]+=int(bool(p["second_hole"])); item["com_lombo"]+=int(bool(p["loin"]))
    return list(groups.values())

@router.post("/descargas/{download_id}/romaneio")
def commercial_manifest(download_id: int, request: ManifestRequest, db: Session = Depends(get_db)):
    pieces=[dict(r) for r in db.execute(text("SELECT peso_kg AS weight_kg,segundo_furo AS second_hole,lombo AS loin FROM pecas WHERE id_descarga=:id"),{"id":download_id}).mappings().all()]
    return {"download_id":download_id,**manifest(pieces,request.prices.model_dump())}

@router.get("/descargas/{download_id}/export.csv")
def export_csv(download_id: int, db: Session = Depends(get_db)):
    rows=db.execute(text("SELECT numero_peca,peso_kg,categoria,segundo_furo,lombo,destino,data_registro FROM pecas WHERE id_descarga=:id ORDER BY numero_peca"),{"id":download_id}).mappings().all()
    if not rows: raise HTTPException(404,"Descarga sem peças")
    stream=io.StringIO(); writer=csv.DictWriter(stream,fieldnames=list(rows[0].keys()),delimiter=";"); writer.writeheader(); writer.writerows([dict(r) for r in rows])
    return StreamingResponse(iter(["\ufeff"+stream.getvalue()]),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":f"attachment; filename=descarga_{download_id}.csv"})

@router.post("/descargas/{download_id}/relatorio.pdf")
def export_pdf(download_id: int, request: ManifestRequest, db: Session = Depends(get_db)):
    dl=db.execute(text("SELECT barco,proprietario,data_hora FROM descargas WHERE id=:id"),{"id":download_id}).mappings().first()
    if not dl: raise HTTPException(404,"Descarga não encontrada")
    pieces=[dict(r) for r in db.execute(text("SELECT peso_kg AS weight_kg,segundo_furo AS second_hole,lombo AS loin FROM pecas WHERE id_descarga=:id"),{"id":download_id}).mappings().all()]
    sd=dashboard_summary(pieces); md=manifest(pieces,request.prices.model_dump()); buffer=io.BytesIO(); pdf=canvas.Canvas(buffer,pagesize=A4); _,height=A4; y=height-50
    pdf.setFont("Helvetica-Bold",16); pdf.drawString(40,y,"NAVIMAR PESCADOS - Relatório de descarga"); y-=30; pdf.setFont("Helvetica",10)
    for line in [f"Barco: {dl['barco']}",f"Proprietário: {dl['proprietario']}",f"Data: {dl['data_hora']}",f"Peças: {sd['pieces']}",f"Peso total: {sd['total_kg']:.2f} kg",f"Média: {sd['average_kg']:.2f} kg",f"Valor estimado: R$ {md['total_value']:.2f}"]:
        pdf.drawString(40,y,line); y-=18
    y-=10; pdf.setFont("Helvetica-Bold",11); pdf.drawString(40,y,"Romaneio comercial"); y-=20; pdf.setFont("Helvetica",9)
    for item in md["items"]:
        pdf.drawString(40,y,f"{item['category']}: {item['kg']:.2f} kg x R$ {item['price_per_kg']:.2f} = R$ {item['total']:.2f}"); y-=16
    pdf.save(); buffer.seek(0)
    return StreamingResponse(buffer,media_type="application/pdf",headers={"Content-Disposition":f"attachment; filename=romaneio_{download_id}.pdf"})
