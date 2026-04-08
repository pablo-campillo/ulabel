async def test_full_labeling_workflow(client, seed_users):
    admin_id = seed_users["admin_id"]
    labeler_id = seed_users["labeler_id"]

    # 1. Login as admin
    resp = await client.post("/v1/token", json={"username": "admin"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"
    assert resp.json()["id"] == str(admin_id)

    # 2. Create project
    resp = await client.post(
        "/v1/projects",
        json={
            "owner_id": str(admin_id),
            "name": "Dogs vs Cats",
            "description": "Classify images as dog or cat",
            "labels": ["dog", "cat"],
        },
    )
    assert resp.status_code == 201
    project = resp.json()
    project_id = project["id"]
    assert project["name"] == "Dogs vs Cats"
    assert set(project["labels"]) == {"dog", "cat"}

    # 3. Add labeler to project
    resp = await client.post(
        f"/v1/projects/{project_id}/labelers",
        json={
            "labeler_id": str(labeler_id),
        },
    )
    assert resp.status_code == 200
    assert len(resp.json()["labelers"]) == 1

    # 4. Register image by storage key
    resp = await client.post(
        f"/v1/projects/{project_id}/images",
        json={
            "storage_key": "datasets/img001.jpg",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"

    # 5. Login as labeler
    resp = await client.post("/v1/token", json={"username": "labeler1"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "labeler"

    # 6. Create assignment (get next pending image)
    resp = await client.post(
        f"/v1/projects/{project_id}/assignments",
        json={
            "labeler_id": str(labeler_id),
        },
    )
    assert resp.status_code == 201
    assignment = resp.json()
    image_id = assignment["id"]
    assignment_id = assignment["assignment_id"]
    assert assignment["status"] == "in_progress"
    assert "presigned_url" in assignment

    # 7. Submit label
    resp = await client.post(
        f"/v1/projects/{project_id}/images/{image_id}/label",
        json={
            "labeler_id": str(labeler_id),
            "assignment_id": assignment_id,
            "label": "cat",
        },
    )
    assert resp.status_code == 201
    label_resp = resp.json()
    assert label_resp["label"] == "cat"
    assert label_resp["labeler_count"] == 1
    assert label_resp["ranking"] == 1
    assert label_resp["total_labelers"] == 1

    # 8. Verify stats
    resp = await client.get(f"/v1/projects/{project_id}/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total_images"] == 1
    assert stats["labeled_images"] == 1

    # 9. No more pending images
    resp = await client.post(
        f"/v1/projects/{project_id}/assignments",
        json={
            "labeler_id": str(labeler_id),
        },
    )
    assert resp.status_code == 204


async def test_update_project_with_multiple_labelers(client, seed_multiple_labelers):
    """Updating a project with multiple labelers should persist all of them."""
    admin_id = seed_multiple_labelers["admin_id"]
    labeler_ids = seed_multiple_labelers["labeler_ids"]

    # 1. Create project
    resp = await client.post(
        "/v1/projects",
        json={
            "owner_id": str(admin_id),
            "name": "Multi Labeler Test",
            "description": "Test assigning multiple labelers",
            "labels": ["a", "b"],
        },
    )
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    # 2. Update project with 5 labelers (same flow as the frontend)
    resp = await client.patch(
        f"/v1/projects/{project_id}",
        json={
            "labeler_ids": [str(lid) for lid in labeler_ids],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["labelers"]) == len(labeler_ids), (
        f"Expected {len(labeler_ids)} labelers but got {len(data['labelers'])}: {data['labelers']}"
    )

    # 3. Verify by fetching the project again
    resp = await client.get(f"/v1/projects/{project_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["labelers"]) == len(labeler_ids), (
        f"After re-fetch: expected {len(labeler_ids)} labelers but got {len(data['labelers'])}"
    )
    returned_ids = {lab["id"] for lab in data["labelers"]}
    expected_ids = {str(lid) for lid in labeler_ids}
    assert returned_ids == expected_ids
