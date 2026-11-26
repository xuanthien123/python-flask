"""create password reset token table

Revision ID: c3f1a7d29b54
Revises: a9eb3de240a8
Create Date: 2026-11-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3f1a7d29b54'
down_revision = 'a9eb3de240a8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('password_reset_token',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('used_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token_hash')
    )
    op.create_index(op.f('ix_password_reset_token_user_id'), 'password_reset_token', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_password_reset_token_user_id'), table_name='password_reset_token')
    op.drop_table('password_reset_token')
