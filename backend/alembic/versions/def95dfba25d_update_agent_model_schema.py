"""update_agent_model_schema

Revision ID: def95dfba25d
Revises: a8d3a3c1ce66
Create Date: 2026-09-03 10:13:28.023665

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'def95dfba25d'
down_revision: Union[str, Sequence[str], None] = 'a8d3a3c1ce66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    with op.batch_alter_table('agents') as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(length=255), nullable=False, server_default='Agent'))
        batch_op.add_column(sa.Column('availability', sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column('max_workload', sa.Integer(), nullable=False, server_default='10'))
        batch_op.add_column(sa.Column('performance_score', sa.Float(), nullable=False, server_default='95.0'))
        batch_op.add_column(sa.Column('average_resolution_time', sa.Float(), nullable=False, server_default='4.0'))
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.alter_column('employee_id', existing_type=sa.VARCHAR(length=50), nullable=True)
        batch_op.create_index(batch_op.f('ix_agents_department_id'), ['department_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_agents_team_id'), ['team_id'], unique=False)
        batch_op.drop_column('full_name')
        batch_op.drop_column('is_online')
        batch_op.drop_column('max_active_tickets')

def downgrade() -> None:
    with op.batch_alter_table('agents') as batch_op:
        batch_op.add_column(sa.Column('max_active_tickets', sa.INTEGER(), nullable=True, server_default='10'))
        batch_op.add_column(sa.Column('is_online', sa.BOOLEAN(), nullable=True, server_default=sa.true()))
        batch_op.add_column(sa.Column('full_name', sa.VARCHAR(length=255), nullable=True, server_default='Agent'))
        batch_op.drop_index(batch_op.f('ix_agents_team_id'))
        batch_op.drop_index(batch_op.f('ix_agents_department_id'))
        batch_op.drop_column('is_active')
        batch_op.drop_column('average_resolution_time')
        batch_op.drop_column('performance_score')
        batch_op.drop_column('max_workload')
        batch_op.drop_column('availability')
        batch_op.drop_column('name')
