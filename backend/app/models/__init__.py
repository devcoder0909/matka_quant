"""
Project Trinetra - ORM Models Package.

Importing all models here ensures they are registered with the
SQLAlchemy metadata before init_db() is called.
"""

from app.models.market import Market  # noqa: F401
from app.models.historical_result import HistoricalResult  # noqa: F401
from app.models.chart_import import ChartImport, ImportErrorRecord  # noqa: F401
from app.models.analysis import (  # noqa: F401
    AnalysisRun,
    CandidateScore,
    ModelVersion,
    ModelMetric,
    BacktestRun,
    BacktestResult,
    FeatureSnapshot,
)
from app.models.admin import AdminUser, AuditLog, SystemSetting  # noqa: F401
