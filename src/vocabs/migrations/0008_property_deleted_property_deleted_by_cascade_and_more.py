# Generated by Django 5.0.4 on 2024-05-06 18:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vocabs", "0007_alter_term_options_property_created_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="deleted",
            field=models.DateTimeField(db_index=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="property",
            name="deleted_by_cascade",
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name="term",
            name="deleted",
            field=models.DateTimeField(db_index=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="term",
            name="deleted_by_cascade",
            field=models.BooleanField(default=False, editable=False),
        ),
    ]