from app.services.business import classify_weight, commercial_class, dashboard_summary, manifest

def test_weight_boundaries():
    assert classify_weight(14.99).startswith("< 15")
    assert classify_weight(15) == "15-24kg"
    assert classify_weight(25) == "25-39kg"
    assert classify_weight(40) == "40kg Exportação"

def test_commercial_priority():
    assert commercial_class({"weight_kg":45,"second_hole":True,"loin":True}) == "2 FURO"
    assert commercial_class({"weight_kg":45,"second_hole":False,"loin":True}) == "LOMBO"

def test_summary_empty_and_values():
    assert dashboard_summary([])["pieces"] == 0
    result=dashboard_summary([{"weight_kg":40,"second_hole":False,"loin":False},{"weight_kg":20,"second_hole":True,"loin":False}])
    assert result["total_kg"] == 60
    assert result["export_kg"] == 40

def test_manifest_prices():
    result=manifest([{"weight_kg":20,"second_hole":False,"loin":False}],{"kg_15_24":25})
    assert result["total_value"] == 500
