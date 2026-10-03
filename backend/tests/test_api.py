def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ai_enabled"] is False


def test_dashboard(client):
    d = client.get("/api/dashboard").json()
    assert d["kpis"]["total_shipments"] == 8
    assert d["kpis"]["compliance_alerts"] >= 1  # seeded denied-party consignee
    assert any(i["type"] == "delay" for i in d["insights"])


def test_shipment_crud_and_events(client):
    payload = {
        "origin_country": "cn", "destination_country": "us", "exporter_name": "Acme Exports",
        "importer_name": "Widget Imports", "incoterm": "FOB", "mode": "sea", "freight_cost": 1000,
        "items": [{"description": "Cotton t-shirts", "hs_code": "6109.10", "quantity": 100, "unit_value": 5}],
    }
    r = client.post("/api/shipments", json=payload)
    assert r.status_code == 201, r.text
    s = r.json()
    assert s["reference"].startswith("TF-")
    assert s["origin_country"] == "CN"
    assert s["goods_value"] == 500
    assert s["events"][0]["status"] == "booked"

    r = client.patch(f"/api/shipments/{s['id']}", json={"status": "in_transit"})
    assert r.json()["status"] == "in_transit"
    assert len(r.json()["events"]) == 2

    r = client.post(f"/api/shipments/{s['id']}/events", json={"status": "customs", "location": "LA"})
    assert r.json()["status"] == "customs"

    assert any(x["id"] == s["id"] for x in client.get("/api/shipments?q=Acme").json())
    assert client.delete(f"/api/shipments/{s['id']}").status_code == 204
    assert client.get(f"/api/shipments/{s['id']}").status_code == 404


def test_classify_keyword_fallback(client):
    r = client.post("/api/classify", json={"description": "Men's knitted cotton t-shirt", "destination_country": "US"})
    body = r.json()
    assert body["engine"] == "keyword"
    assert body["candidates"][0]["hs_code"] == "6109.10"
    assert body["candidates"][0]["duty_rate"] == 0.165


def test_duty_us_fob_basis(client):
    r = client.post("/api/duty/estimate", json={
        "origin_country": "CN", "destination_country": "US", "incoterm": "FOB", "mode": "sea",
        "freight_cost": 1000, "insurance_cost": 100,
        "lines": [{"hs_code": "6109.10", "value": 10000}],
    })
    d = r.json()
    assert d["valuation_basis"] == "FOB"
    assert d["customs_value"] == 10000
    assert d["total_duty"] == 1650
    names = [f["name"] for f in d["fees"]]
    assert any("MPF" in n for n in names) and any("HMF" in n for n in names)
    assert d["landed_cost"] == round(10000 + 1100 + d["total_taxes_and_duties"], 2)


def test_duty_uk_cif_with_vat(client):
    d = client.post("/api/duty/estimate", json={
        "origin_country": "VN", "destination_country": "GB", "incoterm": "CIF",
        "freight_cost": 500, "insurance_cost": 50,
        "lines": [{"hs_code": "6109.10", "value": 10550}],
    }).json()
    assert d["valuation_basis"] == "CIF"
    assert d["customs_value"] == 10550
    assert d["total_duty"] == 1266
    assert d["import_tax"] == round((10550 + 1266) * 0.20, 2)


def test_duty_fta_preference(client):
    d = client.post("/api/duty/estimate", json={
        "origin_country": "MX", "destination_country": "US", "incoterm": "FOB", "claim_preference": True,
        "lines": [{"hs_code": "6109.10", "value": 1000}],
    }).json()
    assert d["fta_applied"] == "USMCA"
    assert d["total_duty"] == 0


def test_compliance_screen(client):
    r = client.post("/api/compliance/screen", json={
        "parties": [{"name": "Northern Star Shipping Company", "country": "KP"}],
        "hs_codes": ["8542.31"],
    })
    d = r.json()
    assert d["status"] == "blocked"
    cats = {f["category"] for f in d["findings"]}
    assert {"Embargo", "Denied party", "Controlled goods"} <= cats

    clear = client.post("/api/compliance/screen", json={"parties": [{"name": "Acme Widgets", "country": "DE"}]}).json()
    assert clear["status"] == "clear"


def test_shipment_documents_and_duty(client):
    sid = client.get("/api/shipments").json()[0]["id"]
    for doc in ["commercial-invoice", "packing-list", "certificate-of-origin"]:
        r = client.get(f"/api/shipments/{sid}/documents/{doc}")
        assert r.status_code == 200 and "<table>" in r.text
    assert client.get(f"/api/shipments/{sid}/documents/bogus").status_code == 404
    assert client.get(f"/api/shipments/{sid}/duty").status_code == 200
    assert client.get(f"/api/shipments/{sid}/compliance").status_code == 200


def test_extract_regex_fallback(client):
    text = """COMMERCIAL INVOICE
Exporter: Saigon Garment Co
Importer: Northern Threads Ltd
Terms: CIF Felixstowe   Currency: USD
Cotton T-shirts | 500 | 4.20
Denim jeans | 200 | 9.50
"""
    d = client.post("/api/documents/extract", json={"text": text}).json()
    assert d["engine"] == "regex"
    assert d["exporter_name"] == "Saigon Garment Co"
    assert d["incoterm"] == "CIF" and d["currency"] == "USD"
    assert len(d["items"]) == 2 and d["items"][0]["quantity"] == 500


def test_assistant_offline(client):
    r = client.post("/api/assistant/chat", json={"messages": [{"role": "user", "content": "Explain FOB vs CIF"}]})
    d = r.json()
    assert d["engine"] == "offline"
    assert "Incoterms" in d["reply"]


def test_duty_unclassified_line(client):
    d = client.post("/api/duty/estimate", json={
        "origin_country": "CN", "destination_country": "GB", "incoterm": "CIF",
        "lines": [{"description": "Mystery widget", "hs_code": "", "value": 100}],
    }).json()
    assert d["lines"][0]["hs_code"] == "—"
    assert any("Mystery widget" in w for w in d["warnings"])
