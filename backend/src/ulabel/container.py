import os
from datetime import timedelta

from dependency_injector import containers, providers

from ulabel.application.add_image_to_project import AddImageToProjectUseCase
from ulabel.application.import_images_from_storage import ImportImagesFromStorageUseCase
from ulabel.application.upload_image_to_project import UploadImageToProjectUseCase
from ulabel.application.add_labeler_to_project import AddLabelerToProjectUseCase
from ulabel.application.create_project import CreateProjectUseCase
from ulabel.application.expire_images_task import ExpireImagesTask
from ulabel.application.get_labeler_projects import GetLabelerProjectsUseCase
from ulabel.application.get_next_image import GetNextImageUseCase
from ulabel.application.login import LoginUseCase
from ulabel.application.export_labels import ExportLabelsUseCase
from ulabel.application.get_project_stats import GetProjectStatsUseCase
from ulabel.application.submit_label import SubmitLabelUseCase
from ulabel.infrastructure.database import build_engine, build_sessionmaker
from ulabel.infrastructure.repositories.sqlalchemy_image_repository import SqlAlchemyImageRepository
from ulabel.infrastructure.repositories.sqlalchemy_label_repository import SqlAlchemyLabelRepository
from ulabel.infrastructure.repositories.sqlalchemy_project_repository import SqlAlchemyProjectRepository
from ulabel.infrastructure.repositories.sqlalchemy_stats_repository import SqlAlchemyStatsRepository
from ulabel.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from ulabel.infrastructure.storage.s3_storage_service import S3StorageService


class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(
        modules=[
            "ulabel.api.routers.tokens",
            "ulabel.api.routers.projects",
            "ulabel.api.routers.images",
            "ulabel.api.routers.labelers",
            "ulabel.api.routers.exports",
            "ulabel.api.routers.stats",
        ]
    )

    engine = providers.Singleton(
        build_engine,
        database_url=providers.Object(
            os.getenv("DATABASE_URL", "postgresql+asyncpg://ulabel:secret@localhost:5432/ulabel")
        ),
    )

    sessionmaker = providers.Singleton(build_sessionmaker, engine=engine)

    user_repository = providers.Factory(SqlAlchemyUserRepository, sessionmaker=sessionmaker)
    project_repository = providers.Factory(SqlAlchemyProjectRepository, sessionmaker=sessionmaker)
    image_repository = providers.Factory(SqlAlchemyImageRepository, sessionmaker=sessionmaker)
    label_repository = providers.Factory(SqlAlchemyLabelRepository, sessionmaker=sessionmaker)
    stats_repository = providers.Factory(SqlAlchemyStatsRepository, sessionmaker=sessionmaker)

    storage_service = providers.Singleton(
        S3StorageService,
        endpoint=providers.Object(os.getenv("STORAGE_ENDPOINT", "localhost:9000")),
        access_key=providers.Object(os.getenv("STORAGE_ACCESS_KEY", "minioadmin")),
        secret_key=providers.Object(os.getenv("STORAGE_SECRET_KEY", "minioadmin")),
        bucket=providers.Object(os.getenv("STORAGE_BUCKET", "ulabel")),
        secure=providers.Object(os.getenv("STORAGE_SECURE", "false").lower() == "true"),
    )

    login_use_case = providers.Factory(LoginUseCase, user_repository=user_repository)

    create_project_use_case = providers.Factory(
        CreateProjectUseCase,
        user_repository=user_repository,
        project_repository=project_repository,
    )

    add_labeler_to_project_use_case = providers.Factory(
        AddLabelerToProjectUseCase,
        user_repository=user_repository,
        project_repository=project_repository,
    )

    add_image_to_project_use_case = providers.Factory(
        AddImageToProjectUseCase,
        project_repository=project_repository,
        image_repository=image_repository,
    )

    upload_image_to_project_use_case = providers.Factory(
        UploadImageToProjectUseCase,
        project_repository=project_repository,
        image_repository=image_repository,
        storage_service=storage_service,
    )

    get_labeler_projects_use_case = providers.Factory(
        GetLabelerProjectsUseCase,
        user_repository=user_repository,
        project_repository=project_repository,
    )

    get_next_image_use_case = providers.Factory(
        GetNextImageUseCase,
        project_repository=project_repository,
        image_repository=image_repository,
    )

    import_images_use_case = providers.Factory(
        ImportImagesFromStorageUseCase,
        project_repository=project_repository,
        image_repository=image_repository,
        storage_service=storage_service,
    )

    submit_label_use_case = providers.Factory(
        SubmitLabelUseCase,
        project_repository=project_repository,
        image_repository=image_repository,
        label_repository=label_repository,
        stats_repository=stats_repository,
    )

    export_labels_use_case = providers.Factory(
        ExportLabelsUseCase,
        project_repository=project_repository,
        label_repository=label_repository,
        storage_service=storage_service,
    )

    get_project_stats_use_case = providers.Factory(
        GetProjectStatsUseCase,
        project_repository=project_repository,
        stats_repository=stats_repository,
    )

    expire_images_task = providers.Factory(
        ExpireImagesTask,
        image_repository=image_repository,
        timeout=providers.Object(timedelta(minutes=30)),
        interval=providers.Object(timedelta(minutes=5)),
    )
