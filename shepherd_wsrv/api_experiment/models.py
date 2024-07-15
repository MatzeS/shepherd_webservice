from enum import Enum
from uuid import uuid4

from beanie import Document
from pydantic import UUID4
from pydantic import Field
from shepherd_core.data_models import Experiment

from shepherd_wsrv.api_user.models import User


class StatusXP(int, Enum):
    inactive = 2
    scheduled = 8
    active = 32
    postprocessing = 128
    finished = 512
    error = 2048
    to_be_deleted = 4096
    # this leaves some wiggle room for extensions


class WebExperiment(Document, Experiment):
    id: UUID4 = Field(default_factory=uuid4)

    status: StatusXP = StatusXP.inactive

    # TODO: temporary bugfixing
    # owner_id: Optional[IdInt] = None

    @classmethod
    async def activate(cls, xp_id: int, user: User) -> bool:
        _xp = await cls.find_one(
            cls.id == xp_id,
            cls.owner_id == user.id,
            cls.status == StatusXP.inactive,
        )
        if not _xp:
            return False
        # TODO: add to scheduler, check if successful
        _xp.status = StatusXP.active
        await _xp.save()
        return True

    @classmethod
    async def get_by_id(cls, xp_id: int, user: User) -> "None | WebExperiment":
        return await cls.find_one(
            cls.id == xp_id,
            cls.owner_id == user.id,
            cls.status != StatusXP.to_be_deleted,
        )

    @classmethod
    async def get_by_user(cls, user: User) -> list["WebExperiment"]:
        return await cls.find(
            cls.owner_id == user.id,
            cls.status != StatusXP.to_be_deleted,
        ).to_list()

    @classmethod
    async def set_to_delete(cls, xp_id: int, user: User) -> bool:
        _xp = await cls.find_one(
            cls.id == xp_id,
            cls.owner_id == user.id,
            cls.status != StatusXP.to_be_deleted,
        )
        if not _xp:
            return False
        _xp.status = StatusXP.to_be_deleted
        await _xp.save()
        return True
