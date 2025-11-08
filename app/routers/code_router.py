# app/routers/code_router.py
from app.routers.base import BaseRouter
from app.models.postgres import Code
from app.services.postgres import CodeService
from app.schemas.postgres import (
    CodeCreate, CodeRead, CodePatch, CodeDelete, CodePaginationRead
)


class CodeRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            prefix="/codes",
            tags=["codes"],
            service=CodeService,
            model=Code,
            create_schema=CodeCreate,
            read_schema=CodeRead,
            patch_schema=CodePatch,
            delete_schema=CodeDelete,
            pagination_schema=CodePaginationRead
        )
