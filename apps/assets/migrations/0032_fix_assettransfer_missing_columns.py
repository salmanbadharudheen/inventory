"""
Safety migration: add all columns that migration 0022 should have added but
may have been skipped due to a duplicate-AddField error on is_deleted.
Each ALTER TABLE is wrapped in IF NOT EXISTS so it is idempotent.
"""
from django.conf import settings
from django.db import migrations


def _add_col_if_missing(cursor, table, column, col_def):
    """Add a column to a table only if it doesn't already exist."""
    cursor.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = '{table}' AND column_name = '{column}'
            ) THEN
                ALTER TABLE {table} ADD COLUMN {column} {col_def};
            END IF;
        END $$;
    """)


def add_missing_columns(apps, schema_editor):
    db = schema_editor.connection.vendor
    if db != 'postgresql':
        # SQLite (local dev) — skip; Django ORM migrations handle it
        return

    with schema_editor.connection.cursor() as cursor:
        t = 'assets_assettransfer'

        # ── from migration 0022 ───────────────────────────────────────────────
        _add_col_if_missing(cursor, t, 'request_by_id',
            'integer NULL REFERENCES users_user(id) DEFERRABLE INITIALLY DEFERRED')
        _add_col_if_missing(cursor, t, 'movement_reason',
            "varchar(255) NOT NULL DEFAULT ''")
        _add_col_if_missing(cursor, t, 'transferred_from_building_id',
            'integer NULL REFERENCES locations_building(id) DEFERRABLE INITIALLY DEFERRED')
        _add_col_if_missing(cursor, t, 'transferred_from_company_id',
            'integer NULL REFERENCES assets_company(id) DEFERRABLE INITIALLY DEFERRED')
        _add_col_if_missing(cursor, t, 'transferred_from_custodian_id',
            'integer NULL REFERENCES assets_custodian(id) DEFERRABLE INITIALLY DEFERRED')
        _add_col_if_missing(cursor, t, 'transferred_from_floor_id',
            'integer NULL REFERENCES locations_floor(id) DEFERRABLE INITIALLY DEFERRED')
        _add_col_if_missing(cursor, t, 'transferred_from_region_id',
            'integer NULL REFERENCES locations_region(id) DEFERRABLE INITIALLY DEFERRED')
        _add_col_if_missing(cursor, t, 'transferred_from_room_id',
            'integer NULL REFERENCES locations_room(id) DEFERRABLE INITIALLY DEFERRED')
        _add_col_if_missing(cursor, t, 'transferred_from_site_id',
            'integer NULL REFERENCES locations_site(id) DEFERRABLE INITIALLY DEFERRED')

        # ── from migration 0023 ───────────────────────────────────────────────
        _add_col_if_missing(cursor, t, 'requester_name',
            "varchar(255) NOT NULL DEFAULT ''")


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0031_add_is_tagged_to_asset'),
    ]

    operations = [
        migrations.RunPython(add_missing_columns, migrations.RunPython.noop),
    ]
