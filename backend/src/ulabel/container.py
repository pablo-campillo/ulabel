from datetime import timedelta
from pathlib import Path

from dependency_injector import containers, providers

from ulabel.application.add_image_to_project import AddImageToProjectUseCase
from ulabel.application.add_labeler_to_project import AddLabelerToProjectUseCase
from ulabel.application.create_assignment import CreateAssignmentUseCase
from ulabel.application.create_project import CreateProjectUseCase
from ulabel.application.expire_images_task import ExpireImagesTask
from ulabel.application.export_labels import ExportLabelsUseCase
from ulabel.application.get_labeler_projects import GetLabelerProjectsUseCase
from ulabel.application.get_project_stats import GetProjectStatsUseCase
from ulabel.application.import_images_from_storage import ImportImagesFromStorageUseCase
from ulabel.application.list_projects import ListProjectsUseCase
from ulabel.application.login import LoginUseCase
from ulabel.application.search_labelers import SearchLabelersUseCase
from ulabel.application.submit_label import SubmitLabelUseCase
from ulabel.application.update_project import UpdateProjectUseCase
from ulabel.application.upload_image_to_project import UploadImageToProjectUseCase
from ulabel.infrastructure.database import build_engine, build_sessionmaker
from ulabel.infrastructure.observability.logging import configure_logging
from ulabel.infrastructure.observability.tracing import setup_tracing
from ulabel.infrastructure.repositories.sqlalchemy_image_repository import SqlAlchemyImageRepository
from ulabel.infrastructure.repositories.sqlalchemy_label_repository import SqlAlchemyLabelRepository
from ulabel.infrastructure.repositories.sqlalchemy_project_repository import (
    SqlAlchemyProjectRepository,
)
from ulabel.infrastructure.repositories.sqlalchemy_stats_repository import SqlAlchemyStatsRepository
from ulabel.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from ulabel.infrastructure.storage.s3_storage_service import S3StorageService

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.yml"


class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(
        modules=[
            "ulabel.api.routers.tokens",
            "ulabel.api.routers.projects",
            "ulabel.api.routers.images",
            "ulabel.api.routers.assignments",
            "ulabel.api.routers.labelers",
            "ulabel.api.routers.exports",
            "ulabel.api.routers.stats",
        ]
    )

    config = providers.Configuration(yaml_files=[str(CONFIG_PATH)])

    logging_setup = providers.Resource(
        configure_logging,
        log_level=config.observability.log_level,
        log_format=config.observability.log_format,
        service_name=config.observability.service_name,
    )

    tracer_provider = providers.Resource(
        setup_tracing,
        service_name=config.observability.service_name,
        endpoint=config.observability.tracing.endpoint,
        enabled=config.observability.tracing.enabled,
        sample_ratio=config.observability.tracing.sample_ratio,
        force_trace_header=config.observability.tracing.force_trace_header,
    )

    engine = providers.Singleton(
        build_engine,
        database_url=config.database.url,
        pool_size=config.database.pool_size.as_int(),
        max_overflow=config.database.max_overflow.as_int(),
        pool_recycle=config.database.pool_recycle.as_int(),
    )

    sessionmaker = providers.Singleton(build_sessionmaker, engine=engine)

    user_repository = providers.Factory(SqlAlchemyUserRepository, sessionmaker=sessionmaker)
    project_repository = providers.Factory(SqlAlchemyProjectRepository, sessionmaker=sessionmaker)
    image_repository = providers.Factory(SqlAlchemyImageRepository, sessionmaker=sessionmaker)
    label_repository = providers.Factory(SqlAlchemyLabelRepository, sessionmaker=sessionmaker)
    stats_repository = providers.Factory(SqlAlchemyStatsRepository, sessionmaker=sessionmaker)

    storage_service = providers.Singleton(
        S3StorageService,
        endpoint=config.storage.endpoint,
        access_key=config.storage.access_key,
        secret_key=config.storage.secret_key,
        bucket=config.storage.bucket,
        secure=config.storage.secure,
        public_endpoint=config.storage.public_endpoint,
    )

    login_use_case = providers.Factory(LoginUseCase, user_repository=user_repository)

    create_project_use_case = providers.Factory(
        CreateProjectUseCase,
        user_repository=user_repository,
        project_repository=project_repository,
    )

    list_projects_use_case = providers.Factory(
        ListProjectsUseCase,
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

    create_assignment_use_case = providers.Factory(
        CreateAssignmentUseCase,
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

    update_project_use_case = providers.Factory(
        UpdateProjectUseCase,
        user_repository=user_repository,
        project_repository=project_repository,
    )

    search_labelers_use_case = providers.Factory(
        SearchLabelersUseCase,
        user_repository=user_repository,
    )

    get_project_stats_use_case = providers.Factory(
        GetProjectStatsUseCase,
        project_repository=project_repository,
        stats_repository=stats_repository,
    )

    expire_images_task = providers.Factory(
        ExpireImagesTask,
        image_repository=image_repository,
        timeout=config.tasks.image_assignment_timeout_seconds.as_(
            lambda s: timedelta(seconds=int(s))
        ),
        interval=config.tasks.image_expiry_interval_seconds.as_(
            lambda s: timedelta(seconds=int(s))
        ),
    )
