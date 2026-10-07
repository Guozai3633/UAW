"""Versioned records, idempotent requests and durable events. Reviewed initial schema."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "uaw_records",
        sa.Column("principal_id", sa.String(128), primary_key=True),
        sa.Column("namespace", sa.String(128), primary_key=True),
        sa.Column("resource_id", sa.String(128), primary_key=True),
        sa.Column("revision", sa.BigInteger(), nullable=False),
        sa.Column("schema_name", sa.String(128), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("deleted", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("revision > 0", name="ck_records_revision"),
    )
    op.create_table(
        "uaw_requests",
        sa.Column("principal_id", sa.String(128), primary_key=True),
        sa.Column("namespace", sa.String(128), primary_key=True),
        sa.Column("resource_id", sa.String(128), primary_key=True),
        sa.Column("request_id", sa.String(128), primary_key=True),
        sa.Column("parameter_hash", sa.String(64), nullable=False),
        sa.Column("result", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "uaw_outbox",
        sa.Column("event_id", sa.String(128), primary_key=True),
        sa.Column("principal_id", sa.String(128), nullable=False),
        sa.Column("stream_id", sa.String(128), nullable=False),
        sa.Column("seq", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("principal_id", "stream_id", "seq", name="uq_outbox_seq"),
        sa.CheckConstraint("seq > 0", name="ck_outbox_seq"),
    )
    op.create_index("ix_uaw_outbox_principal_id", "uaw_outbox", ["principal_id"])
    op.create_table(
        "uaw_consumer_receipts",
        sa.Column("principal_id", sa.String(128), primary_key=True),
        sa.Column("consumer_id", sa.String(128), primary_key=True),
        sa.Column("event_id", sa.String(128), primary_key=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    # Destructive rollback is an explicit operator action, never an application startup step.
    op.drop_table("uaw_consumer_receipts")
    op.drop_table("uaw_outbox")
    op.drop_table("uaw_requests")
    op.drop_table("uaw_records")

