from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from ulabel.application.expire_images_task import ExpireImagesTask
from ulabel.domain.images import Image, ImageStatus
from ulabel.infrastructure.repositories.in_memory.image_repository import InMemoryImageRepository

TIMEOUT = timedelta(minutes=30)
NOW = datetime(2026, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
EXPIRED_AT = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
RECENT_AT = datetime(2026, 1, 1, 12, 45, 0, tzinfo=timezone.utc)


def make_image(project_id, assigned_at=None):
    image = Image.create(id=uuid4(), project_id=project_id, storage_key="img.jpg")
    if assigned_at:
        image.assign(labeler_id=uuid4(), assigned_at=assigned_at)
    return image


@pytest.fixture
def project_id():
    return uuid4()


@pytest.fixture
def expired_image(project_id):
    return make_image(project_id, assigned_at=EXPIRED_AT)


@pytest.fixture
def recent_image(project_id):
    return make_image(project_id, assigned_at=RECENT_AT)


@pytest.fixture
def pending_image(project_id):
    return make_image(project_id)


@pytest.fixture
def repo(expired_image, recent_image, pending_image):
    return InMemoryImageRepository(images=[expired_image, recent_image, pending_image])


@pytest.fixture
def task(repo):
    return ExpireImagesTask(
        image_repository=repo,
        timeout=TIMEOUT,
        interval=timedelta(minutes=5),
        now=lambda: NOW,
    )


async def test_expired_image_is_reset_to_pending(task, repo, expired_image):
    await task.tick()
    assert repo._images[expired_image.id].status == ImageStatus.PENDING


async def test_expired_image_loses_assignment(task, repo, expired_image):
    await task.tick()
    image = repo._images[expired_image.id]
    assert image.labeler_id is None
    assert image.assigned_at is None
    assert image.assignment_id is None


async def test_recent_image_is_not_expired(task, repo, recent_image):
    await task.tick()
    assert repo._images[recent_image.id].status == ImageStatus.IN_PROGRESS


async def test_pending_image_is_not_touched(task, repo, pending_image):
    await task.tick()
    assert repo._images[pending_image.id].status == ImageStatus.PENDING
    assert repo._images[pending_image.id].assignment_id is None
