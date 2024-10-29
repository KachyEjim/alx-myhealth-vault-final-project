"""empty message

Revision ID: cec2a607ae2b
Revises: 1de1b794e701
Create Date: 2024-10-29 01:24:18.797066

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cec2a607ae2b'
down_revision = '1de1b794e701'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('medications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_sent_period', sa.String(length=20), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('medications', schema=None) as batch_op:
        batch_op.drop_column('last_sent_period')

    # ### end Alembic commands ###
