from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = 'f9b08bf69a06'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Commands to create the tables
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('phone_number', sa.String(length=20)),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'keyword',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('keyword', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Commands to drop the tables
    op.drop_table('user')
    op.drop_table('keyword')
