"""membership billing enhancements

Revision ID: 20260425_membership_billing
Revises:
Create Date: 2026-04-25
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260425_membership_billing"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE members
        ADD COLUMN IF NOT EXISTS aadhaar_no VARCHAR(20),
        ADD COLUMN IF NOT EXISTS pan_no VARCHAR(20);
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_members_aadhaar_no ON members (aadhaar_no);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_members_pan_no ON members (pan_no);")

    op.execute(
        """
        ALTER TABLE membership_plans
        ADD COLUMN IF NOT EXISTS plan_type VARCHAR(50) NOT NULL DEFAULT 'monthly',
        ADD COLUMN IF NOT EXISTS registration_fee NUMERIC(10, 2) NOT NULL DEFAULT 0.00;
        """
    )

    op.execute(
        """
        ALTER TABLE member_subscriptions
        ADD COLUMN IF NOT EXISTS total_pause_days INTEGER NOT NULL DEFAULT 0,
        ADD COLUMN IF NOT EXISTS last_pause_date DATE,
        ADD COLUMN IF NOT EXISTS last_resume_date DATE;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id UUID PRIMARY KEY,
            invoice_no VARCHAR(50) NOT NULL UNIQUE,
            branch_id UUID NOT NULL REFERENCES branches(id),
            member_id UUID NOT NULL REFERENCES members(id),
            subscription_id UUID REFERENCES member_subscriptions(id),
            invoice_type VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'issued',
            subtotal NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            registration_fee NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            discount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            tax NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            total_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            amount_paid NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            amount_due NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            due_date DATE NOT NULL,
            notes TEXT,
            created_by_staff_id UUID NOT NULL REFERENCES staff(id),
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_invoices_invoice_no ON invoices (invoice_no);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_invoices_branch_id ON invoices (branch_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_invoices_member_id ON invoices (member_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_invoices_subscription_id ON invoices (subscription_id);")

    op.execute(
        """
        ALTER TABLE payments
        ADD COLUMN IF NOT EXISTS invoice_id UUID REFERENCES invoices(id);
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_payments_invoice_id ON payments (invoice_id);")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS subscription_pause_history (
            id UUID PRIMARY KEY,
            branch_id UUID NOT NULL REFERENCES branches(id),
            member_id UUID NOT NULL REFERENCES members(id),
            subscription_id UUID NOT NULL REFERENCES member_subscriptions(id),
            pause_date DATE NOT NULL,
            resume_date DATE,
            pause_days INTEGER NOT NULL DEFAULT 0,
            reason TEXT,
            created_by_staff_id UUID NOT NULL REFERENCES staff(id),
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_subscription_pause_history_subscription_id ON subscription_pause_history (subscription_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_subscription_pause_history_member_id ON subscription_pause_history (member_id);"
    )


def downgrade() -> None:
    # Intentionally conservative for production safety.
    pass
