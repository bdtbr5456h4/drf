# Generated by Django 4.2 on 2023-04-09 13:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('link', '0004_alter_link_user'),
    ]

    operations = [
        migrations.DeleteModel(
            name='User',
        ),
    ]
