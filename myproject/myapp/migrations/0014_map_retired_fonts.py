"""Map retired font stacks to the curated enterprise set (see RETIRED_FONT_MAP)."""

from django.db import migrations


def map_retired_fonts(apps, schema_editor):
    ThemeSettings = apps.get_model("myapp", "ThemeSettings")
    # Import here (not at module top) so the migration always uses the map
    # as it exists at migration time, not a future edited version.
    from myapp.models import RETIRED_FONT_MAP

    for old_stack, new_stack in RETIRED_FONT_MAP.items():
        ThemeSettings.objects.filter(heading_font=old_stack).update(heading_font=new_stack)
        ThemeSettings.objects.filter(body_font=old_stack).update(body_font=new_stack)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0013_alter_themesettings_body_font_and_more"),
    ]

    operations = [
        migrations.RunPython(map_retired_fonts, noop),
    ]
