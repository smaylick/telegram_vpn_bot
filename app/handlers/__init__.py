from aiogram import Router

from app.handlers import (
    admin,
    admin_add,
    admin_broadcast,
    admin_price,
    common,
    info,
    member,
)


def build_router() -> Router:
    router = Router()
    # FSM handlers must be registered before the generic member/admin text handlers,
    # otherwise the text the admin types inside a state will be matched by another
    # handler first.
    router.include_router(admin_add.router)
    router.include_router(admin_price.router)
    router.include_router(admin_broadcast.router)
    router.include_router(common.router)
    router.include_router(info.router)
    router.include_router(member.router)
    router.include_router(admin.router)
    return router
