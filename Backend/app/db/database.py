"""Database engine configuration with production-grade pooling."""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _normalized_database_url(url: str) -> str:
    """Normalize DB URL for production managed Postgres providers."""
    if not settings.is_production:
        return url
    if "sslmode=" in url:
        return url

    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["sslmode"] = "require"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def create_db_engine() -> Engine:
    engine = create_engine(
        _normalized_database_url(settings.database_url),
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle,
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def _set_statement_timeout(dbapi_connection, _connection_record) -> None:
        # Soft guard against runaway queries (seconds); 0 = disabled
        timeout = settings.db_statement_timeout_seconds
        if timeout and timeout > 0:
            cursor = dbapi_connection.cursor()
            cursor.execute(f"SET statement_timeout = '{int(timeout * 1000)}'")
            cursor.close()

    return engine


engine = create_db_engine()


def check_connection() -> bool:
    """Return True if the database accepts connections."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Database connection check failed", extra={"event": "database_error"})
        return False
