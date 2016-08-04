# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-03 22:34
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Agency',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('lang', models.CharField(max_length=2)),
                ('name', models.CharField(max_length=80)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField()),
                ('timezone', models.CharField(max_length=80)),
                ('url', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='HistoricalAgency',
            fields=[
                ('id', models.IntegerField(db_index=True)),
                ('lang', models.CharField(max_length=2)),
                ('name', models.CharField(max_length=80)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField()),
                ('timezone', models.CharField(max_length=80)),
                ('url', models.URLField()),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical agency',
            },
        ),
    ]
