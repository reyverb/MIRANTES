from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(prefix="/api/reports", tags=["Relatórios"])


class LandingRecord(BaseModel):
    id: int
    landing_date: date | None = None
    vessel_name: str | None = None
    species: str | None = None
    weight_kg: float | None = None
    port: str | None = None
    status: str | None = None


class LandingListResponse(BaseModel):
    items: list[LandingRecord]
    total: int
    page: int
    page_size: int
    total_weight_kg: float


def _base_filters(
    data_inicio: date | None,
    data_fim: date | None,
    embarcacao: str | None,
    especie: str | None,
    status: str | None,
) -> tuple[str, dict[str, Any]]:
    conditions = []
    params: dict[str, Any] = {
        "data_inicio": data_inicio.isoformat() if data_inicio else None,
        "data_fim": data_fim.isoformat() if data_fim else None,
        "embarcacao": embarcacao,
        "especie": especie,
        "status": status,
    }

    if data_inicio:
        conditions.append("d.data_hora >= CAST(:data_inicio AS timestamptz)")

    if data_fim:
        conditions.append(
            "d.data_hora < CAST(:data_fim AS timestamptz) + INTERVAL '1 day'"
        )

    if embarcacao:
        conditions.append("d.barco ILIKE '%' || :embarcacao || '%'")

    if especie:
        conditions.append("p.categoria ILIKE '%' || :especie || '%'")

    if status:
        conditions.append("d.status = :status")

    where_clause = "".join(conditions) if conditions else "TRUE"
    return where_clause, params


@router.get("/landings", response_model=LandingListResponse)
async def listar_descargas(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    embarcacao: str | None = None,
    especie: str | None = None,
    porto: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    if page < 1:
        raise HTTPException(status_code=400, detail="A página deve ser maior ou igual a 1.")

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=400,
            detail="O tamanho da página deve estar entre 1 e 100.",
        )

    where_clause, params = _base_filters(
        data_inicio=data_inicio,
        data_fim=data_fim,
        embarcacao=embarcacao,
        especie=especie,
        status=status,
    )

    count_sql = text(
        """
        SELECT COUNT(*)
        FROM (
            SELECT d.id
            FROM public.descargas d
            LEFT JOIN public.pecas p ON p.id_descarga = d.id
            WHERE """ + where_clause + """
            GROUP BY d.id
        ) AS total
        """
    )

    total = db.execute(count_sql, params).scalar() or 0

    query_params = {
        **params,
        "limit": page_size,
        "offset": (page - 1) * page_size,
    }

    list_sql = text(
        """
        SELECT
            d.id,
            d.data_hora AS landing_date,
            d.barco AS vessel_name,
            d.status,
            COALESCE(SUM(p.peso_kg), 0) AS weight_kg,
            COUNT(p.id) AS pieces
        FROM public.descargas d
        LEFT JOIN public.pecas p ON p.id_descarga = d.id
        WHERE """ + where_clause + """
        GROUP BY d.id, d.data_hora, d.barco, d.status
        ORDER BY d.data_hora DESC
        LIMIT :limit OFFSET :offset
        """
    )

    rows = db.execute(list_sql, query_params).mappings().all()

    items = [
        LandingRecord(
            id=row["id"],
            landing_date=row["landing_date"].date() if row["landing_date"] else None,
            vessel_name=row["vessel_name"],
            species=None,
            weight_kg=float(row["weight_kg"] or 0),
            port=None,
            status=row["status"],
        )
        for row in rows
    ]

    total_weight = sum(item.weight_kg or 0 for item in items)

    return LandingListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_weight_kg=total_weight,
    )


@router.get("/landings/summary")
async def resumo_descargas(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    embarcacao: str | None = None,
    especie: str | None = None,
    porto: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    where_clause, params = _base_filters(
        data_inicio=data_inicio,
        data_fim=data_fim,
        embarcacao=embarcacao,
        especie=especie,
        status=status,
    )

    query_sql = text(
        """
        SELECT
            d.id,
            d.data_hora,
            d.barco,
            d.status,
            p.categoria,
            p.peso_kg
        FROM public.descargas d
        LEFT JOIN public.pecas p ON p.id_descarga = d.id
        WHERE """ + where_clause + """
        """
    )

    rows = db.execute(query_sql, params).mappings().all()

    descargas = {row["id"]: row for row in rows}
    total_records = len(descargas)

    by_species: dict[str, float] = {}
    by_vessel: dict[str, float] = {}
    by_date: dict[str, float] = {}
    total_weight = 0.0

    for row in rows:
        weight = float(row["peso_kg"] or 0)
        species = row["categoria"] or "Não informado"
        vessel = row["barco"] or "Não informado"
        landing_date = row["data_hora"].date().isoformat() if row["data_hora"] else "Não informado"

        if weight:
            total_weight += weight
            by_species[species] = by_species.get(species, 0) + weight
            by_vessel[vessel] = by_vessel.get(vessel, 0) + weight
            by_date[landing_date] = by_date.get(landing_date, 0) + weight

    return {
        "total_records": total_records,
        "total_weight_kg": round(total_weight, 2),
        "average_weight_kg": (
            round(total_weight / total_records, 2)
            if total_records
            else 0
        ),
        "by_species": [
            {"label": label, "value": value}
            for label, value in sorted(
                by_species.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ],
        "by_vessel": [
            {"label": label, "value": value}
            for label, value in sorted(
                by_vessel.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ],
        "by_date": [
            {"label": label, "value": value}
            for label, value in sorted(by_date.items())
        ],
    }
