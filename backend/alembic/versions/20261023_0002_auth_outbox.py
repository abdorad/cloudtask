"""add users, task ownership, and durable outbox

Revision ID: 20261023_0002
Revises: 20261022_0001
Create Date: 2026-10-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261023_0002"
down_revision = "20261022_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.add_column("tasks", sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_tasks_owner_id_users", "tasks", "users", ["owner_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_tasks_owner_id", "tasks", ["owner_id"], unique=False)
    op.create_table(
        "outbox_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )
    op.create_index("ix_outbox_messages_task_id", "outbox_messages", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_outbox_messages_task_id", table_name="outbox_messages")
    op.drop_table("outbox_messages")
    op.drop_index("ix_tasks_owner_id", table_name="tasks")
    op.drop_constraint("fk_tasks_owner_id_users", "tasks", type_="foreignkey")
    op.drop_column("tasks", "owner_id")
    op.drop_table("users")
