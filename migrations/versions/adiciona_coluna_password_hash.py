from alembic import op
import sqlalchemy as sa

revision = 'adiciona_coluna_password_hash'
down_revision = 'af71a703a667'  # Certifique-se de que este valor é o correto
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('password_hash', sa.String(length=128), nullable=False))

def downgrade():
    op.drop_column('users', 'password_hash')
