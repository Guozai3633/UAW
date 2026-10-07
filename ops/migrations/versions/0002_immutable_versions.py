"""Retain immutable record revisions; deletion denies access to prior revisions."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0002_immutable_versions"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "uaw_record_versions",
        sa.Column("principal_id", sa.String(128), primary_key=True),
        sa.Column("namespace", sa.String(128), primary_key=True),
        sa.Column("resource_id", sa.String(128), primary_key=True),
        sa.Column("revision", sa.BigInteger(), primary_key=True),
        sa.Column("schema_name", sa.String(128), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("revision > 0", name="ck_record_versions_revision"),
    )
    # Existing accepted rows also need a version snapshot. Tombstones stay unreadable.
    op.execute(sa.text(
        "INSERT INTO uaw_record_versions "
        "(principal_id, namespace, resource_id, revision, schema_name, payload, created_at) "
        "SELECT principal_id, namespace, resource_id, revision, schema_name, payload, updated_at "
        "FROM uaw_records"
    ))


def downgrade() -> None:
    op.drop_table("uaw_record_versions")
