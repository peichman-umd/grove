# Generated by Django 5.0.4 on 2024-05-07 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vocabs", "0008_property_deleted_property_deleted_by_cascade_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="vocabulary",
            name="published",
            field=models.DateTimeField(editable=False, null=True),
        ),
    ]
