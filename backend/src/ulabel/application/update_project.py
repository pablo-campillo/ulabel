"""Use case for updating an existing labeling project."""

from uuid import UUID

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.application.create_project import ProjectNameAlreadyExists, Unauthorized
from ulabel.application.login import UserNotFound
from ulabel.domain.ports.unit_of_work import UnitOfWork
from ulabel.domain.projects import Project
from ulabel.domain.users import UserRole


class UpdateProjectUseCase:
    """Updates project metadata and labeler assignments.

    Validates name uniqueness and labeler roles before persisting changes.
    """

    def __init__(self, uow: UnitOfWork):
        """Initialize the use case.

        Args:
            uow: Unit of Work for transactional repository access.
        """
        self._uow = uow

    async def execute(
        self,
        project_id: UUID,
        *,
        name: str | None = None,
        description: str | None = None,
        labeler_ids: set[UUID] | None = None,
    ) -> Project:
        """Update a project's name, description, and/or labeler assignments.

        Args:
            project_id: The ID of the project to update.
            name: New project name, or None to keep the current name.
            description: New description, or None to keep the current description.
            labeler_ids: New set of labeler IDs, or None to keep the current set.

        Returns:
            The updated project entity.

        Raises:
            ProjectNotFound: If the project does not exist.
            ProjectNameAlreadyExists: If the new name conflicts with another project.
            UserNotFound: If a labeler ID does not correspond to an existing user.
            Unauthorized: If a labeler ID belongs to a non-labeler user.
        """
        async with self._uow as uow:
            project = await uow.project_repository.get_by_id(project_id)
            if project is None:
                raise ProjectNotFound("Project not found")

            if name is not None and name != project.name:
                existing = await uow.project_repository.get_by_name(name)
                if existing is not None:
                    raise ProjectNameAlreadyExists("Project name already exists")

            project.update(name=name, description=description)

            if labeler_ids is not None:
                users = await uow.user_repository.get_by_ids(labeler_ids)
                if len(users) != len(labeler_ids):
                    raise UserNotFound("Labeler not found")
                if any(u.role != UserRole.LABELER for u in users):
                    raise Unauthorized("User is not a labeler")
                project.set_labelers(labeler_ids)

            await uow.project_repository.save(project)
            await uow.commit()
            return project
