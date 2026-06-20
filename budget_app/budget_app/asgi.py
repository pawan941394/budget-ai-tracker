import os
import sys
from pathlib import Path

from django.core.asgi import get_asgi_application
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "budget_app.settings")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

django_application = get_asgi_application()

from budget_users.api import router as budget_users_router
from budget_transactions.api import router as budget_transactions_router
from budget_llmapikey.api import router as budget_llmapikey_router
from ai_Chat_bot.ai_part.api import router as budget_chat_router

fastapi_application = FastAPI(title="Budget App")
fastapi_application.include_router(budget_users_router)
fastapi_application.include_router(budget_transactions_router)
fastapi_application.include_router(budget_llmapikey_router)
fastapi_application.include_router(budget_chat_router)


async def healthcheck(request):
    return JSONResponse({"status": "ok"})


application = Starlette(
    routes=[
        Route("/health", healthcheck),
        Mount("/api", app=fastapi_application),
        Mount("/", app=django_application),
    ]
)
application = ASGIStaticFilesHandler(application)
