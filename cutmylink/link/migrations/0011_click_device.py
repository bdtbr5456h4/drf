# Generated by Django 4.2 on 2023-04-09 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('link', '0010_link_redirect_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='click',
            name='device',
            field=models.CharField(default='PC', max_length=255),
        ),
    ]
