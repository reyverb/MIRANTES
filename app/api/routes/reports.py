from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.database import get_supabase_client

router = APIRouter(prefix="/api/reports", tags=["Relatórios"])


class LandingRecord(BaseModel):
    id: str | int
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


def _build_filters(
    data_inicio: date | None,
    data_fim: date | None,
    embarcacao: str | None,
    especie: str | None,
    porto: str | None,
    status: str | None,
) -> dict[str, Any]:
    filters: dict[str, Any] = {}

    if data_inicio:
        filters["landing_date"] = f"gte.{data_inicio.isoformat()}"

    if data_fim:
        if "landing_date" in filters:
            filters["landing_date"] += f",lte.{data_fim.isoformat()}"
        else:
            filters["landing_date"] = f"lte.{data_fim.isoformat()}"

    if embarcacao:
        filters["vessel_name"] = f"ilike.%{embarcacao}%"

    if especie:
        filters["species"] = f"ilike.%{especie}%"

    if porto:
        filters["port"] = f"ilike.%{porto}%"

    if status:
        filters["status"] = f"eq.{status}"

    return filters


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
):
    if page < 1:
        raise HTTPException(status_code=400, detail="A página deve ser maior ou igual a 1.")

    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="O tamanho da página deve estar entre 1 e 100.")

    try:
        supabase = get_supabase_client()
        query = supabase.table("landings").select("*", count="exact")

        filters = _build_filters(
            data_inicio=data_inicio,
            data_fim=data_fim,
            embarcacao=embarcacao,
            especie=especie,
            porto=porto,
            status=status,
        )

        for field, value in filters.items():
            query = query.filter(field, "filter", value)

        start = (page - 1) * page_size
        end = start + page_size - 1

        response = query.order("landing_date", desc=True).range(start, end).execute()
        records = response.data or []
        total = response.count or 0

        total_weight = sum(float(record.get("weight_kg") or 0) for record in records)

        return LandingListResponse(
            items=[LandingRecord(**record) for record in records],
            total=total,
            page=page,
            page_size=page_size,
            total_weight_kg=total_weight,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Não foi possível carregar os dados de descarga: {exc}",
        ) from exc


@router.get("/landings/summary")
async def resumo_descargas(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    embarcacao: str | None = None,
    especie: str | None = None,
    porto: str | None = None,
    status: str | None = None,
):
    try:
        supabase = get_supabase_client()
        query = supabase.table("landings").select(
            "landing_date,vessel_name,species,weight_kg,port,status"
        )

        filters = _build_filters(
            data_inicio=data_inicio,
            data_fim=data_fim,
            embarcacao=embarcacao,
            especie=especie,
            porto=porto,
            status=status,
        )

        for field, value in filters.items():
            query = query.filter(field, "filter", value)

        response = query.execute()
        records = response.data or []

        total_records = len(records)
        total_weight = sum(float(record.get("weight_kg") or 0) for record in records)

        by_species: dict[str, float] = {}
        by_vessel: dict[str, float] = {}
        by_date: dict[str, float] = {}

        for record in records:
            species = record.get("species") or "Não informado"
            vessel = record.get("vessel_name") or "Não informado"
            landing_date = record.get("landing_date") or "Não informado"
            weight = float(record.get("weight_kg") or 0)

            by_species[species] = by_species.get(species, 0) + weight
            by_vessel[vessel] = by_vessel.get(vessel, 0) + weight
            by_date[landing_date] = by_date.get(landing_date, 0) + weight

        return {
            "total_records": total_records,
            "total_weight_kg": total_weight,
            "average_weight_kg": round(total_weight / total_records, 2) if total_records else 0,
            "by_species": [
                {"label": label, "value": value}
                for label, value in sorted(by_species.items(), key=lambda item: item[1], reverse=True)
            ],
            "by_vessel": [
                {"label": label, "value": value}
                for label, value in sorted(by_vessel.items(), key=lambda item: item[1], reverse=True)
            ],
            "by_date": [
                {"label": label, "value": value}
                for label, value in sorted(by_date.items())
            ],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Não foi possível gerar o resumo dos dados: {exc}",
        ) from exc
