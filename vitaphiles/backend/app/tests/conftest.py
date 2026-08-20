import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-not-for-production")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-secret-not-for-production")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5174")
os.environ.setdefault("ENVIRONMENT", "test")
