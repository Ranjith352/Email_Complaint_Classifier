"""update_user_model_schema

Revision ID: de57b279d9b1
Revises: 0afcd021c06f
Create Date: 2026-09-03 10:02:02.595925

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'de57b279d9b1'
down_revision: Union[str, Sequence[str], None] = '0afcd021c06f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(length=255), nullable=False, server_default='User'))
        batch_op.add_column(sa.Column('password_hash', sa.String(length=255), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('department_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('team_id', sa.Integer(), nullable=True))
        batch_op.alter_column('role', existing_type=sa.VARCHAR(length=50), nullable=False)
        batch_op.alter_column('is_active', existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.create_index(batch_op.f('ix_users_role'), ['role'], unique=False)
        batch_op.create_foreign_key('fk_users_team_id', 'teams', ['team_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_users_department_id', 'departments', ['department_id'], ['id'], ondelete='SET NULL')
        batch_op.drop_column('hashed_password')
        batch_op.drop_column('full_name')

def downgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('full_name', sa.VARCHAR(length=255), nullable=True))
        batch_op.add_column(sa.Column('hashed_password', sa.VARCHAR(length=255), nullable=True))
        batch_op.drop_constraint('fk_users_department_id', type_='foreignkey')
        batch_op.drop_constraint('fk_users_team_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_users_role'))
        batch_op.alter_column('is_active', existing_type=sa.BOOLEAN(), nullable=True)
        batch_op.alter_column('role', existing_type=sa.VARCHAR(length=50), nullable=True)
        batch_op.drop_column('team_id')
        batch_op.drop_column('department_id')
        batch_op.drop_column('password_hash')
        batch_op.drop_column('name')
