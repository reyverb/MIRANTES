from collections import defaultdict


def classify_weight(weight: float) -> str:
    if weight < 15:
        return "< 15 kg · Refugo/Local"
    if weight < 25:
        return "15-24kg"
    if weight < 40:
        return "25-39kg"
    return "40kg Exportação"


def commercial_class(piece: dict) -> str:
    if piece.get("second_hole"):
        return "2 FURO"
    if piece.get("loin"):
        return "LOMBO"
    weight = float(piece["weight_kg"])
    if weight >= 40:
        return "40KG ACIMA"
    if weight >= 25:
        return "25KG - 39KG"
    return "15KG - 24KG"


def dashboard_summary(pieces: list[dict]) -> dict:
    count = len(pieces)
    total = sum(float(p["weight_kg"]) for p in pieces)
    export_kg = sum(float(p["weight_kg"]) for p in pieces if float(p["weight_kg"]) >= 40)
    holes = sum(bool(p.get("second_hole")) for p in pieces)
    loins = sum(bool(p.get("loin")) for p in pieces)
    return {"pieces": count, "total_kg": round(total, 2), "average_kg": round(total / count, 2) if count else 0, "export_kg": round(export_kg, 2), "export_percent": round(export_kg / total * 100, 2) if total else 0, "second_hole_count": holes, "second_hole_percent": round(holes / count * 100, 2) if count else 0, "loin_count": loins}


def manifest(pieces: list[dict], prices: dict) -> dict:
    keys = {"15KG - 24KG": "kg_15_24", "25KG - 39KG": "kg_25_39", "40KG ACIMA": "kg_40_up", "2 FURO": "second_hole", "LOMBO": "loin"}
    grouped = defaultdict(float)
    for piece in pieces:
        grouped[commercial_class(piece)] += float(piece["weight_kg"])
    lines = []
    for category, price_key in keys.items():
        kg = round(grouped[category], 2)
        price = float(prices.get(price_key, 0))
        lines.append({"category": category, "kg": kg, "price_per_kg": price, "total": round(kg * price, 2)})
    return {"items": lines, "total_kg": round(sum(x["kg"] for x in lines), 2), "total_value": round(sum(x["total"] for x in lines), 2)}
