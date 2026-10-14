from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("gis", "0001_initial"),
        ("core", "0001_extensions"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS gis_poi_earth_gist ON gis_poi USING gist (ll_to_earth(lat, lng));",
            reverse_sql="DROP INDEX IF EXISTS gis_poi_earth_gist;",
        ),
    ]
