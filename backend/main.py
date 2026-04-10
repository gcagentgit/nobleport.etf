"""
NoblePort Backend - Main Application Entry Point

FastAPI application serving as the Python/Linux backend for NoblePort Networks.
Provides REST APIs for construction project management, Buildertrend integration,
Stripe payment processing, and bridge services to the NoblePort ETF tokenization platform.

Revenue Loop: Lead → Proposal → Deposit → Job → Scheduled → Completed → Paid
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.health import router as health_router
from backend.api.leads import router as leads_router
from backend.api.projects import router as projects_router
from backend.api.schedules import router as schedules_router
from backend.api.invoices import router as invoices_router
from backend.api.buildertrend import router as buildertrend_router
from backend.api.sync import router as sync_router
from backend.api.bridge import router as bridge_router
from backend.api.proposals import router as proposals_router
from backend.api.stripe_webhooks import router as stripe_router
from backend.api.jobs import router as jobs_router
from backend.api.change_orders import router as change_orders_router
from backend.api.intake import router as intake_router
from backend.api.dashboard import router as dashboard_router
from backend.config.database import init_db
from backend.config.settings import settings
from backend.services.reminder_scheduler import ReminderScheduler
from backend.services.sync_engine import SyncEngine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    await init_db()

    # Buildertrend sync engine
    sync_engine = SyncEngine()
    app.state.sync_engine = sync_engine

    if settings.buildertrend_sync_mode.value == "scheduled":
        await sync_engine.start_scheduled_sync()

    # Payment reminder scheduler (daily cron)
    reminder_scheduler = ReminderScheduler()
    app.state.reminder_scheduler = reminder_scheduler
    await reminder_scheduler.start()

    yield

    if hasattr(app.state, "sync_engine"):
        await app.state.sync_engine.stop()
    if hasattr(app.state, "reminder_scheduler"):
        await app.state.reminder_scheduler.stop()


app = FastAPI(
    title="NoblePort Backend",
    description=(
        "Python/Linux backend for NoblePort Networks. "
        "Full revenue loop: proposals, Stripe payments, job pipeline, "
        "Buildertrend sync, and NoblePort ETF bridge."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(proposals_router, prefix="/api/proposals", tags=["Proposals"])
app.include_router(stripe_router, prefix="/api/stripe", tags=["Stripe"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(change_orders_router, prefix="/api/jobs", tags=["Change Orders"])
app.include_router(leads_router, prefix="/api/leads", tags=["Leads"])
app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
app.include_router(schedules_router, prefix="/api/schedules", tags=["Schedules"])
app.include_router(invoices_router, prefix="/api/invoices", tags=["Invoices"])
app.include_router(intake_router, prefix="/api/intake", tags=["Avatar Intake"])
app.include_router(buildertrend_router, prefix="/api/buildertrend", tags=["Buildertrend"])
app.include_router(sync_router, prefix="/api/sync", tags=["Sync"])
app.include_router(bridge_router, prefix="/api/bridge", tags=["NoblePort Bridge"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
