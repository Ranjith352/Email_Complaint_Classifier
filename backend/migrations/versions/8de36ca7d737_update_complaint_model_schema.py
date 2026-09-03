"""update_complaint_model_schema

Revision ID: 8de36ca7d737
Revises: def95dfba25d
Create Date: 2026-09-03 10:18:09.243135

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8de36ca7d737'
down_revision: Union[str, Sequence[str], None] = 'def95dfba25d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    with op.batch_alter_table('complaint_events') as batch_op:
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=False, server_default='Event logged'))
        batch_op.add_column(sa.Column('event_metadata', sa.JSON(), nullable=True))
        batch_op.alter_column('event_type', existing_type=sa.VARCHAR(length=100), type_=sa.String(length=50))
        batch_op.alter_column('actor', existing_type=sa.VARCHAR(length=255), type_=sa.String(length=100))
        batch_op.drop_column('notes')
        batch_op.drop_column('metadata_json')

    with op.batch_alter_table('complaint_feedback') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.alter_column('is_category_correct', existing_type=sa.BOOLEAN(), nullable=False, server_default=sa.true())
        batch_op.alter_column('is_sentiment_correct', existing_type=sa.BOOLEAN(), nullable=False, server_default=sa.true())
        batch_op.create_foreign_key('fk_complaint_feedback_user_id', 'users', ['user_id'], ['id'], ondelete='SET NULL')
        batch_op.drop_column('agent_id')

    with op.batch_alter_table('complaints') as batch_op:
        batch_op.add_column(sa.Column('complaint_number', sa.String(length=50), nullable=False, server_default='CMP-000'))
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=False, server_default='Complaint description'))
        batch_op.add_column(sa.Column('priority', sa.String(length=50), nullable=False, server_default='P3'))
        batch_op.add_column(sa.Column('ai_confidence', sa.Float(), nullable=False, server_default='0.90'))
        batch_op.add_column(sa.Column('review_required', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('ai_status', sa.String(length=50), nullable=False, server_default='COMPLETED'))
        batch_op.add_column(sa.Column('summary', sa.Text(), nullable=True))
        batch_op.alter_column('source', existing_type=sa.VARCHAR(length=50), nullable=False, server_default='WEB')
        batch_op.drop_index('ix_complaints_ticket_number')
        batch_op.create_index(batch_op.f('ix_complaints_assigned_agent_id'), ['assigned_agent_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_complaints_complaint_number'), ['complaint_number'], unique=True)
        batch_op.create_index(batch_op.f('ix_complaints_department_id'), ['department_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_complaints_priority'), ['priority'], unique=False)
        batch_op.create_index(batch_op.f('ix_complaints_source'), ['source'], unique=False)
        batch_op.create_index(batch_op.f('ix_complaints_team_id'), ['team_id'], unique=False)
        batch_op.drop_column('priority_level')
        batch_op.drop_column('ticket_number')
        batch_op.drop_column('body')

def downgrade() -> None:
    pass
