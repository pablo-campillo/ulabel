from uuid import uuid4

import pytest

from tests.unit.conftest import make_uow
from ulabel.application.get_project_stats import (
    GetProjectStatsUseCase,
    ProjectNotFound,
)
from ulabel.domain.images import Image, ImageStatus
from ulabel.domain.labels import LabelRecord
from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory.project_repository import (
    InMemoryProjectRepository,
)
from ulabel.infrastructure.repositories.in_memory.stats_repository import InMemoryStatsRepository


@pytest.fixture
def labeler_a():
    return User.create_labeler(id=uuid4(), username="ana")


@pytest.fixture
def labeler_b():
    return User.create_labeler(id=uuid4(), username="pedro")


@pytest.fixture
def project(admin, labeler_a, labeler_b):
    p = Project.create(
        id=uuid4(), owner=admin, name="Animals", description="desc", labels={"cat", "dog"}
    )
    p.add_labeler(labeler_a.id)
    p.add_labeler(labeler_b.id)
    return p


@pytest.fixture
def images_and_labels(project, labeler_a, labeler_b):
    images = []
    labels = []

    # 3 done images (2 labeled by ana, 1 by pedro)
    for i in range(2):
        img = Image.create(id=uuid4(), project_id=project.id, storage_key=f"ana_{i}.jpg")
        img.status = ImageStatus.DONE
        images.append(img)
        labels.append(
            LabelRecord.create(
                id=uuid4(),
                project_id=project.id,
                image_id=img.id,
                labeler_id=labeler_a.id,
                label="cat",
            )
        )

    img = Image.create(id=uuid4(), project_id=project.id, storage_key="pedro_0.jpg")
    img.status = ImageStatus.DONE
    images.append(img)
    labels.append(
        LabelRecord.create(
            id=uuid4(),
            project_id=project.id,
            image_id=img.id,
            labeler_id=labeler_b.id,
            label="dog",
        )
    )

    # 2 pending images
    for i in range(2):
        images.append(
            Image.create(
                id=uuid4(),
                project_id=project.id,
                storage_key=f"pending_{i}.jpg",
            )
        )

    return images, labels


@pytest.fixture
def use_case(project, images_and_labels, labeler_a, labeler_b):
    images, labels = images_and_labels
    usernames = {labeler_a.id: labeler_a.username, labeler_b.id: labeler_b.username}
    return GetProjectStatsUseCase(
        uow=make_uow(
            project_repository=InMemoryProjectRepository(projects=[project]),
            stats_repository=InMemoryStatsRepository(
                images=images, labels=labels, usernames=usernames
            ),
        ),
    )


async def test_total_images(use_case, project):
    stats = await use_case.execute(project.id)
    assert stats.total_images == 5


async def test_labeled_images(use_case, project):
    stats = await use_case.execute(project.id)
    assert stats.labeled_images == 3


async def test_class_distribution(use_case, project):
    stats = await use_case.execute(project.id)
    assert stats.class_distribution == {"cat": 2, "dog": 1}


async def test_labeler_class_counts(use_case, project, labeler_a, labeler_b):
    stats = await use_case.execute(project.id)
    by_id = {lc.labeler_id: lc for lc in stats.labeler_class_counts}
    assert by_id[labeler_a.id].counts == {"cat": 2}
    assert by_id[labeler_b.id].counts == {"dog": 1}


async def test_raises_when_project_not_found(use_case):
    with pytest.raises(ProjectNotFound):
        await use_case.execute(uuid4())
