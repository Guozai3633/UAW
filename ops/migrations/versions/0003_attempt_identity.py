"""A real attempt cannot hold two reservations under different request IDs."""

import sqlalchemy as sa
from alembic import op

revision = "0003_attempt_identity"
down_revision = "0002_immutable_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_budget_attempt ON uaw_records "
        "(principal_id, (payload->>'attempt_id')) "
        "WHERE namespace = 'budget.accounting' AND NOT deleted"
    ))


def downgrade() -> None:
    op.drop_index("uq_budget_attempt", table_name="uaw_records")
