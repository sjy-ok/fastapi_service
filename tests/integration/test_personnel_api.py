async def test_complete_resource_lifecycle(client):
    person = (
        await client.post("/personnels", json={"w3_account": "zhangsan", "name": "张三", "employee_id": "12345678"})
    ).json()
    assert (await client.get(f"/personnels/{person['id']}")).status_code == 200
    assert (await client.patch(f"/personnels/{person['id']}", json={"name": "张三丰"})).json()["name"] == "张三丰"
    assert (
        await client.post("/personnels", json={"w3_account": "zhangsan", "name": "重复", "employee_id": "other"})
    ).status_code == 409

    tm = (await client.post("/tm-groups", json={"name": "智能运维开发组", "leader_personnel_id": person["id"]})).json()
    pl = (await client.post("/pl-groups", json={"name": "智能驾舱组"})).json()
    department = (await client.post("/departments", json={"name": "MAE-M开发三部"})).json()
    assert (await client.get(f"/tm-groups/{tm['id']}")).json()["leader_personnel_id"] == person["id"]
    assert (await client.patch(f"/pl-groups/{pl['id']}", json={"leader_personnel_id": person["id"]})).status_code == 200
    assert (await client.patch(f"/departments/{department['id']}", json={"name": "集成验证部"})).status_code == 200

    response = await client.post(
        "/personnel-assignments",
        json={
            "personnel_id": person["id"],
            "tm_group_id": tm["id"],
            "pl_group_id": pl["id"],
            "department_id": department["id"],
            "creator": "admin",
            "notes": "初始记录",
        },
    )
    assert response.status_code == 201
    assignment = response.json()
    assert assignment["personnel"]["name"] == "张三丰"
    assert assignment["tm_group"]["name"] == "智能运维开发组"
    assert assignment["department"]["name"] == "集成验证部"
    assert assignment["start_time"] is None

    records = (await client.get(f"/personnel-assignments?personnel_id={person['id']}")).json()
    assert len(records) == 1
    updated = await client.patch(
        f"/personnel-assignments/{assignment['id']}",
        json={"start_time": "2023-01-01", "end_time": "2025-07-28"},
    )
    assert updated.status_code == 200
    assert updated.json()["notes"] == "初始记录"

    assert (await client.delete(f"/personnels/{person['id']}")).status_code == 409
    assert (await client.delete(f"/tm-groups/{tm['id']}")).status_code == 409
    assert (await client.delete(f"/personnel-assignments/{assignment['id']}")).status_code == 204
    assert (await client.patch(f"/tm-groups/{tm['id']}", json={"leader_personnel_id": None})).status_code == 200
    assert (await client.patch(f"/pl-groups/{pl['id']}", json={"leader_personnel_id": None})).status_code == 200
    assert (await client.delete(f"/tm-groups/{tm['id']}")).status_code == 204
    assert (await client.delete(f"/pl-groups/{pl['id']}")).status_code == 204
    assert (await client.delete(f"/departments/{department['id']}")).status_code == 204
    assert (await client.delete(f"/personnels/{person['id']}")).status_code == 204


async def test_assignment_validation_and_optional_organizations(client):
    assert (await client.post("/personnel-assignments", json={"personnel_id": 999})).status_code == 400
    person = (await client.post("/personnels", json={"w3_account": "lisi", "name": "李四", "employee_id": "E2"})).json()
    response = await client.post("/personnel-assignments", json={"personnel_id": person["id"]})
    assert response.status_code == 201
    assert response.json()["tm_group"] is None
    invalid = await client.patch(
        f"/personnel-assignments/{response.json()['id']}",
        json={"start_time": "2025-01-02", "end_time": "2025-01-01"},
    )
    assert invalid.status_code == 400


async def test_organization_leader_validation(client):
    assert (await client.post("/tm-groups", json={"name": "TM", "leader_personnel_id": 999})).status_code == 400
    assert (await client.get("/tm-groups/999")).status_code == 404


async def test_nullable_personnel_fields_and_search(client):
    first = (await client.post("/personnels", json={"w3_account": "zhangsan"})).json()
    second = (await client.post("/personnels", json={"w3_account": "zhangli", "name": "张丽"})).json()
    third = (await client.post("/personnels", json={"w3_account": "lisi", "employee_id": "WX123456"})).json()
    assert first["name"] is None and first["employee_id"] is None
    assert second["employee_id"] is None
    assert (await client.get("/personnels?q=张丽")).json()[0]["id"] == second["id"]
    assert (await client.get("/personnels?q=WX123")).json()[0]["id"] == third["id"]
    fuzzy = (await client.get("/personnels?w3_account=zhang&limit=50")).json()
    assert {item["id"] for item in fuzzy} == {first["id"], second["id"]}
    assert (await client.get("/personnels?limit=0")).status_code == 422
    assert (await client.get("/personnels?limit=201")).status_code == 422


async def test_assignment_global_search(client):
    person = (
        await client.post(
            "/personnels", json={"w3_account": "search_user", "name": "搜索人员", "employee_id": "SEARCH001"}
        )
    ).json()
    tm = (await client.post("/tm-groups", json={"name": "智能搜索组"})).json()
    pl = (await client.post("/pl-groups", json={"name": "工程检索组"})).json()
    department = (await client.post("/departments", json={"name": "数字化体验部"})).json()
    await client.post(
        "/personnel-assignments",
        json={
            "personnel_id": person["id"],
            "tm_group_id": tm["id"],
            "pl_group_id": pl["id"],
            "department_id": department["id"],
            "start_time": "2025-07-01",
            "end_time": "2025-08-01",
            "creator": "creator_w3",
            "notes": "切换部门记录",
        },
    )
    for keyword in (
        "search_user",
        "搜索人员",
        "SEARCH001",
        "智能搜索",
        "工程检索",
        "数字化体验",
        "creator_w3",
        "切换部门",
        "2025-07",
    ):
        response = await client.get("/personnel-assignments", params={"q": keyword})
        assert response.status_code == 200
        assert len(response.json()) == 1, keyword
    assert len((await client.get("/tm-groups?q=智能")).json()) == 1
    assert len((await client.get("/pl-groups?q=工程")).json()) == 1
    assert len((await client.get("/departments?q=数字")).json()) == 1


async def test_unique_organization_names_and_normalization(client):
    tm = (await client.post("/tm-groups", json={"name": "  唯一 TM  "})).json()
    await client.post("/pl-groups", json={"name": "唯一 PL"})
    department = (await client.post("/departments", json={"name": "唯一部门"})).json()
    assert tm["name"] == "唯一 TM"
    assert (await client.post("/tm-groups", json={"name": "唯一 TM"})).status_code == 409
    assert (await client.post("/pl-groups", json={"name": "唯一 PL"})).status_code == 409
    assert (await client.post("/departments", json={"name": "唯一部门"})).status_code == 409
    assert (await client.post("/tm-groups", json={"name": "   "})).status_code == 422
    other = (await client.post("/departments", json={"name": "其他部门"})).json()
    assert (await client.patch(f"/departments/{other['id']}", json={"name": department["name"]})).status_code == 409


async def test_assignment_date_contract(client):
    person = (await client.post("/personnels", json={"w3_account": "date_user"})).json()
    null_start = (
        await client.post("/personnel-assignments", json={"personnel_id": person["id"], "start_time": None})
    ).json()
    old_start = (
        await client.post("/personnel-assignments", json={"personnel_id": person["id"], "start_time": "1900-01-01"})
    ).json()
    same_day = await client.post(
        "/personnel-assignments",
        json={"personnel_id": person["id"], "start_time": "2025-02-25", "end_time": "2025-02-25"},
    )
    assert null_start["start_time"] is None
    assert old_start["start_time"] == "1900-01-01"
    assert same_day.status_code == 201
    invalid = await client.post(
        "/personnel-assignments",
        json={"personnel_id": person["id"], "start_time": "2025-02-26", "end_time": "2025-02-25"},
    )
    assert invalid.status_code == 400
