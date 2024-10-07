from alembic import op
import sqlalchemy as sa

# Revisão identificadora e referências (garanta que os IDs sejam únicos)
revision = 'adiciona_coluna_password_hash'
down_revision = 'af71a703a667'  # Coloque o ID da última migração aqui
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('password_hash', sa.String(length=128), nullable=False))

def downgrade():
    op.drop_column('users', 'password_hash')
