"""empty message

Revision ID: 77fa96322cd1
Revises: 46e3a7b76cd7
Create Date: 2024-10-21 08:03:19.388422

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77fa96322cd1'
down_revision = '46e3a7b76cd7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('appointments', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=50),
               existing_nullable=False)

    with op.batch_alter_table('doctors', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=50),
               existing_nullable=False)

    with op.batch_alter_table('medical_records', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=50),
               existing_nullable=False)

    with op.batch_alter_table('medications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('count', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('count_left', sa.Integer(), nullable=True))
        batch_op.drop_column('med_id')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=50),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)

    with op.batch_alter_table('medications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('med_id', sa.VARCHAR(length=150), autoincrement=False, nullable=False))
        batch_op.drop_column('count_left')
        batch_op.drop_column('count')

    with op.batch_alter_table('medical_records', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)

    with op.batch_alter_table('doctors', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)

    with op.batch_alter_table('appointments', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)

    # ### end Alembic commands ###
