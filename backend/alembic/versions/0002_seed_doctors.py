"""seed a few doctors so the UI is usable on first start

Revision ID: 0002_seed_doctors
Revises: 0001_initial
Create Date: 2026-10-17
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_seed_doctors"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

doctors = sa.table(
    "doctors",
    sa.column("full_name", sa.String),
    sa.column("specialty", sa.String),
    sa.column("room", sa.String),
    sa.column("active", sa.Boolean),
)

SEED = [
    {"full_name": "Dr. Ananya Rao", "specialty": "General Medicine", "room": "101", "active": True},
    {"full_name": "Dr. Kabir Mehta", "specialty": "Pediatrics", "room": "104", "active": True},
    {"full_name": "Dr. Farah Siddiqui", "specialty": "Dermatology", "room": "201", "active": True},
    {"full_name": "Dr. Vikram Nair", "specialty": "Orthopedics", "room": "203", "active": True},
]


def upgrade():
    op.bulk_insert(doctors, SEED)


def downgrade():
    names = [d["full_name"] for d in SEED]
    op.execute(doctors.delete().where(doctors.c.full_name.in_(names)))
