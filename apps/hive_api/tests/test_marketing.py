from fastapi.testclient import TestClient

from apps.hive_api.main import app

client = TestClient(app)


def test_marketing_list_empty():
    r = client.get("/marketing/campaigns")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_marketing_create_and_list_scoped():
    # Create
    payload = {
        "name": "UnitTest Campaign",
        "org_id": "org_ut",
        "brain_id": "brain_marketing",
        "status": "draft",
    }
    r = client.post("/marketing/campaigns", json=payload)
    assert r.status_code == 200
    created = r.json()
    assert created["name"] == payload["name"]
    assert created["status"] == "draft"

    # List scoped
    r2 = client.get(
        "/marketing/campaigns", params={"org_id": "org_ut", "brain_id": "brain_marketing"}
    )
    assert r2.status_code == 200
    items = r2.json()
    assert any(it.get("name") == payload["name"] for it in items)


def test_marketing_assets_and_experiments_crud():
    # Create campaign first
    camp_payload = {
        "name": "UT Campaign 2",
        "org_id": "org_ut2",
        "brain_id": "brain_marketing",
        "status": "draft",
    }
    rc = client.post("/marketing/campaigns", json=camp_payload)
    assert rc.status_code == 200
    camp_id = rc.json()["id"]

    # Create asset
    asset_payload = {
        "campaign_id": camp_id,
        "kind": "copy",
        "name": "headline v1",
        "data": '{"headline":"Amazing"}',
        "org_id": camp_payload["org_id"],
        "brain_id": camp_payload["brain_id"],
    }
    ra = client.post("/marketing/assets", json=asset_payload)
    assert ra.status_code == 200
    asset = ra.json()
    assert asset["campaign_id"] == camp_id
    assert asset["kind"] == "copy"

    # List assets
    la = client.get("/marketing/assets", params={"campaign_id": camp_id})
    assert la.status_code == 200
    assert any(a.get("id") == asset["id"] for a in la.json())

    # Create experiment
    exp_payload = {
        "campaign_id": camp_id,
        "name": "Variant Test",
        "kind": "ab",
        "hypothesis": "Copy A outperforms B",
        "org_id": camp_payload["org_id"],
        "brain_id": camp_payload["brain_id"],
    }
    rexp = client.post("/marketing/experiments", json=exp_payload)
    assert rexp.status_code == 200
    exp = rexp.json()
    assert exp["campaign_id"] == camp_id
    assert exp["kind"] == "ab"

    # List experiments
    lexp = client.get("/marketing/experiments", params={"campaign_id": camp_id})
    assert lexp.status_code == 200
    assert any(e.get("id") == exp["id"] for e in lexp.json())

    # Create experiment result
    res_payload = {
        "experiment_id": exp["id"],
        "variant": "A",
        "metric": "ctr",
        "value": 0.12,
        "sample_size": 1000,
    }
    rres = client.post("/marketing/experiment-results", json=res_payload)
    assert rres.status_code == 200
    res = rres.json()
    assert res["experiment_id"] == exp["id"]
    assert res["metric"] == "ctr"

    # List experiment results
    lres = client.get(
        "/marketing/experiment-results", params={"experiment_id": exp["id"], "metric": "ctr"}
    )
    assert lres.status_code == 200
    assert any(r.get("id") == res["id"] for r in lres.json())


def test_marketing_attribution_and_journeys():
    # Create campaign for scoping inheritance
    camp_payload = {
        "name": "UT Campaign 3",
        "org_id": "org_attr",
        "brain_id": "brain_marketing",
    }
    rc = client.post("/marketing/campaigns", json=camp_payload)
    assert rc.status_code == 200
    camp_id = rc.json()["id"]

    # Create attribution event
    attr_payload = {
        "campaign_id": camp_id,
        "event": "click",
        "source": "google",
        "medium": "cpc",
        "channel": "web",
        "value": 1.0,
        "currency": "USD",
        "customer_ref": "cust-001",
    }
    ra = client.post("/marketing/attribution", json=attr_payload)
    assert ra.status_code == 200
    attr = ra.json()
    assert attr["campaign_id"] == camp_id
    assert attr["event"] == "click"

    # List attribution by campaign
    la = client.get("/marketing/attribution", params={"campaign_id": camp_id, "event": "click"})
    assert la.status_code == 200
    assert any(a.get("id") == attr["id"] for a in la.json())

    # Create customer journey record
    j_payload = {
        "campaign_id": camp_id,
        "customer_ref": "cust-001",
        "stage": "consideration",
        "source": "google",
        "medium": "cpc",
    }
    rj = client.post("/marketing/journeys", json=j_payload)
    assert rj.status_code == 200
    journey = rj.json()
    assert journey["stage"] == "consideration"

    # List journeys
    lj = client.get(
        "/marketing/journeys", params={"campaign_id": camp_id, "customer_ref": "cust-001"}
    )
    assert lj.status_code == 200
    assert any(j.get("id") == journey["id"] for j in lj.json())
