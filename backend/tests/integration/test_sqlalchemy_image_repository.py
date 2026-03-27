from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from ulabel.domain.images import Image, ImageStatus
from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.sqlalchemy_image_repository import SqlAlchemyImageRepository
from ulabel.infrastructure.repositories.sqlalchemy_project_repository import SqlAlchemyProjectRepository
from ulabel.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def repo(sessionmaker):
    return SqlAlchemyImageRepository(sessionmaker)


@pytest.fixture
async def project(sessionmaker) -> Project:
    user_repo = SqlAlchemyUserRepository(sessionmaker)
    project_repo = SqlAlchemyProjectRepository(sessionmaker)
    admin = User.create_admin(id=uuid4(), username="admin")
    await user_repo.save(admin)
    p = Project.create(id=uuid4(), owner=admin, name="Project", description="desc", labels={"cat"})
    await project_repo.save(p)
    return p


@pytest.fixture
async def pending_image(repo, project) -> Image:
    image = Image.create(id=uuid4(), project_id=project.id, storage_key="img/photo.jpg")
    await repo.save(image)
    return image


async def test_save_and_get_next_pending(repo, pending_image, project):
    found = await repo.get_next_pending(project.id)
    assert found is not None
    assert found.id == pending_image.id
    assert found.status == ImageStatus.PENDING


async def test_get_next_pending_returns_none_when_no_images(repo, project):
    assert await repo.get_next_pending(project.id) is None


async def test_save_updates_image_status(repo, pending_image, project):
    pending_image.assign(labeler_id=uuid4(), assigned_at=NOW)
    await repo.save(pending_image)

    found = await repo.get_next_pending(project.id)
    assert found is None  # no more pending images


async def test_get_expired_in_progress(repo, pending_image):
    old_time = NOW - timedelta(hours=2)
    pending_image.assign(labeler_id=uuid4(), assigned_at=old_time)
    await repo.save(pending_image)

    cutoff = NOW - timedelta(minutes=30)
    expired = await repo.get_expired_in_progress(cutoff)
    assert any(i.id == pending_image.id for i in expired)


async def test_get_expired_in_progress_excludes_recent(repo, pending_image):
    recent_time = NOW - timedelta(minutes=10)
    pending_image.assign(labeler_id=uuid4(), assigned_at=recent_time)
    await repo.save(pending_image)

    cutoff = NOW - timedelta(minutes=30)
    expired = await repo.get_expired_in_progress(cutoff)
    assert not any(i.id == pending_image.id for i in expired)


async def test_assignment_id_is_persisted(repo, pending_image):
    pending_image.assign(labeler_id=uuid4(), assigned_at=NOW)
    await repo.save(pending_image)

    all_expired = await repo.get_expired_in_progress(NOW + timedelta(hours=1))
    found = next(i for i in all_expired if i.id == pending_image.id)
    assert found.assignment_id == pending_image.assignment_id
