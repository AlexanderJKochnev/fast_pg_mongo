# app/routers/rawdata_router.py
from app.routers.base import BaseRouter
from app.models.postgres import Rawdata
from app.services.postgres import RawService
from app.schemas.postgres import (
    RawdataCreate, RawdataRead, RawdataPatch, RawdataDelete, RawdataPaginationRead
)


class RawdataRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            prefix="/rawdata",
            tags=["rawdata"],
            service=RawService,
            model=Rawdata,
            create_schema=RawdataCreate,
            read_schema=RawdataRead,
            patch_schema=RawdataPatch,
            delete_schema=RawdataDelete,
            pagination_schema=RawdataPaginationRead
        )
