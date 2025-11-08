# app/routers/image_router.py
from app.routers.base import BaseRouter
from app.models.postgres import Image
from app.services.postgres import ImageService
from app.schemas.postgres import (
    ImageCreate, ImageRead, ImagePatch, ImageDelete, ImagePaginationRead
)


class ImageRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            prefix="/images",
            tags=["images"],
            service=ImageService,
            model=Image,
            create_schema=ImageCreate,
            read_schema=ImageRead,
            patch_schema=ImagePatch,
            delete_schema=ImageDelete,
            pagination_schema=ImagePaginationRead
        )
