"""Initial BookHub schema."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260629_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bookshelf",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(160), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("author", sa.String(120), nullable=False),
        sa.Column("cover", sa.Text(), nullable=False),
        sa.Column("intro", sa.Text(), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("current_source", sa.String(80), nullable=False),
        sa.Column("source_data", sa.Text(), nullable=False),
        sa.Column("display_status", sa.String(30), nullable=False),
        sa.Column("last_read_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("external_id", "current_source", name="uq_book_source"),
    )
    op.create_index("ix_bookshelf_title", "bookshelf", ["title"])
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("identifier", sa.String(80), nullable=False, unique=True),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("healthy", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "search_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cache_key", sa.String(300), nullable=False, unique=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_search_cache_cache_key", "search_cache", ["cache_key"])
    op.create_index("ix_search_cache_expires_at", "search_cache", ["expires_at"])
    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("bookshelf.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(80), nullable=False),
        sa.Column("external_chapter_id", sa.String(160), nullable=False),
        sa.Column("chapter_index", sa.Integer(), nullable=False),
        sa.Column("chapter_name", sa.String(240), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("book_id", "source", "external_chapter_id", name="uq_cached_chapter"),
    )
    op.create_index("ix_chapters_book_id", "chapters", ["book_id"])
    op.create_table(
        "download_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("bookshelf.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("completed", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_download_jobs_book_id", "download_jobs", ["book_id"])


def downgrade() -> None:
    op.drop_table("download_jobs")
    op.drop_table("chapters")
    op.drop_table("search_cache")
    op.drop_table("sources")
    op.drop_table("bookshelf")
