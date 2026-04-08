from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.dialects.postgresql import insert

from ulabel.domain.images import Image, ImageStatus
from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.models.label import LabelRecordModel
from ulabel.infrastructure.repositories.sql.image_repository import SqlAlchemyImageRepository
from ulabel.infrastructure.repositories.sql.project_repository import (
    SqlAlchemyProjectRepository,
)
from ulabel.infrastructure.repositories.sql.stats_repository import SqlAlchemyStatsRepository
from ulabel.infrastructure.repositories.sql.user_repository import SqlAlchemyUserRepository

DAY1 = datetime(2026, 3, 20, 10, 0, 0, tzinfo=timezone.utc)
DAY2 = datetime(2026, 3, 21, 14, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def repo(session):
    return SqlAlchemyStatsRepository(session)


@pytest.fixture
async def admin(session):
    user = User.create_admin(id=uuid4(), username="admin")
    await SqlAlchemyUserRepository(session).save(user)
    return user


@pytest.fixture
async def labeler_ana(session):
    user = User.create_labeler(id=uuid4(), username="ana")
    await SqlAlchemyUserRepository(session).save(user)
    return user


@pytest.fixture
async def labeler_pedro(session):
    user = User.create_labeler(id=uuid4(), username="pedro")
    await SqlAlchemyUserRepository(session).save(user)
    return user


@pytest.fixture
async def project(session, admin, labeler_ana, labeler_pedro):
    proj_repo = SqlAlchemyProjectRepository(session)
    p = Project.create(
        id=uuid4(), owner=admin, name="Animals", description="desc", labels={"cat", "dog"}
    )
    p.add_labeler(labeler_ana.id)
    p.add_labeler(labeler_pedro.id)
    await proj_repo.save(p)
    return p


async def _insert_label(session, *, project_id, image_id, labeler_id, label, created_at):
    stmt = insert(LabelRecordModel).values(
        id=uuid4(),
        project_id=project_id,
        image_id=image_id,
        labeler_id=labeler_id,
        label=label,
        created_at=created_at,
    )
    await session.execute(stmt)


@pytest.fixture
async def seeded_data(session, project, labeler_ana, labeler_pedro):
    """Create 5 images: 3 done (with labels), 2 pending."""
    img_repo = SqlAlchemyImageRepository(session)

    done_images = []
    for i in range(3):
        img = Image.create(id=uuid4(), project_id=project.id, storage_key=f"done_{i}.jpg")
        img.status = ImageStatus.DONE
        await img_repo.save(img)
        done_images.append(img)

    for i in range(2):
        img = Image.create(id=uuid4(), project_id=project.id, storage_key=f"pending_{i}.jpg")
        await img_repo.save(img)

    # ana: 2 labels on day1 (cat, dog), 1 label on day2 (cat)
    await _insert_label(
        session,
        project_id=project.id,
        image_id=done_images[0].id,
        labeler_id=labeler_ana.id,
        label="cat",
        created_at=DAY1,
    )
    await _insert_label(
        session,
        project_id=project.id,
        image_id=done_images[1].id,
        labeler_id=labeler_ana.id,
        label="dog",
        created_at=DAY1,
    )
    await _insert_label(
        session,
        project_id=project.id,
        image_id=done_images[2].id,
        labeler_id=labeler_pedro.id,
        label="cat",
        created_at=DAY2,
    )


async def test_image_counts(repo, project, seeded_data):
    counts = await repo.get_image_counts(project.id)
    assert counts.total == 5
    assert counts.labeled == 3


async def test_labeler_class_counts(repo, project, seeded_data, labeler_ana, labeler_pedro):
    rows = await repo.get_labeler_class_counts(project.id)
    by_key = {(r.labeler_id, r.label): r.count for r in rows}
    assert by_key[(labeler_ana.id, "cat")] == 1
    assert by_key[(labeler_ana.id, "dog")] == 1
    assert by_key[(labeler_pedro.id, "cat")] == 1
    assert len(rows) == 3


async def test_daily_label_counts(repo, project, seeded_data, labeler_ana, labeler_pedro):
    rows = await repo.get_daily_label_counts(project.id)
    by_key = {(r.labeler_id, r.day, r.label): r.count for r in rows}

    # ana: day1 -> cat=1, dog=1
    assert by_key[(labeler_ana.id, date(2026, 3, 20), "cat")] == 1
    assert by_key[(labeler_ana.id, date(2026, 3, 20), "dog")] == 1

    # pedro: day2 -> cat=1
    assert by_key[(labeler_pedro.id, date(2026, 3, 21), "cat")] == 1

    assert len(rows) == 3


async def test_daily_rows_include_username(repo, project, seeded_data, labeler_ana):
    rows = await repo.get_daily_label_counts(project.id)
    ana_rows = [r for r in rows if r.labeler_id == labeler_ana.id]
    assert all(r.username == "ana" for r in ana_rows)


async def test_empty_project_returns_zeros(repo, session, admin):
    proj_repo = SqlAlchemyProjectRepository(session)
    empty = Project.create(id=uuid4(), owner=admin, name="Empty", description="", labels={"x"})
    await proj_repo.save(empty)

    counts = await repo.get_image_counts(empty.id)
    assert counts.total == 0
    assert counts.labeled == 0
    assert await repo.get_labeler_class_counts(empty.id) == []
    assert await repo.get_daily_label_counts(empty.id) == []
