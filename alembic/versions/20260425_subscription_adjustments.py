"""subscription adjustments

Revision ID: 20260425_sub_adjust
Revises: 20260425_membership_billing
Create Date: 2026-04-25
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260425_sub_adjust"
down_revision = "20260425_membership_billing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS subscription_adjustments (
            id UUID PRIMARY KEY,
            branch_id UUID NOT NULL REFERENCES branches(id),
            member_id UUID NOT NULL REFERENCES members(id),
            subscription_id UUID NOT NULL REFERENCES member_subscriptions(id),
            days_delta INTEGER NOT NULL,
            reason TEXT,
            created_by_staff_id UUID NOT NULL REFERENCES staff(id),
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_subscription_adjustments_subscription_id ON subscription_adjustments (subscription_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_subscription_adjustments_member_id ON subscription_adjustments (member_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_subscription_adjustments_branch_id ON subscription_adjustments (branch_id);"
    )


def downgrade() -> None:
    # Intentionally conservative for production safety.
    pass
