"""Use case for updating an existing labeling project."""

from uuid import UUID

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.application.create_project import ProjectNameAlreadyExists, Unauthorized
from ulabel.application.login import UserNotFound
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.projects import Project
from ulabel.domain.users import UserRole



class UpdateProjectUseCase:
    """Updates project metadata and labeler assignments.

    Validates name uniqueness and labeler roles before persisting changes.
    """

    def __init__(self, user_repository: UserRepository, project_repository: ProjectRepository):
        """Initialize the use case.

        Args:
            user_repository: Repository for user lookups.
            project_repository: Repository for project lookups and persistence.
        """
        self.user_repository = user_repository
        self.project_repository = project_repository

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
        project = await self.project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFound("Project not found")

        if name is not None and name != project.name:
            existing = await self.project_repository.get_by_name(name)
            if existing is not None:
                raise ProjectNameAlreadyExists("Project name already exists")

        project.update(name=name, description=description)

        if labeler_ids is not None:
            for labeler_id in labeler_ids:
                user = await self.user_repository.get_by_id(labeler_id)
                if user is None:
                    raise UserNotFound("Labeler not found")
                if user.role != UserRole.LABELER:
                    raise Unauthorized("User is not a labeler")
            project.set_labelers(labeler_ids)

        await self.project_repository.save(project)
        return project
