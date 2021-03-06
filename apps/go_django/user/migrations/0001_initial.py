# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-19 19:09
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fleet', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EndUser',
            fields=[
                ('id', models.CharField(max_length=80, primary_key=True, serialize=False)),
                ('waiver', models.CharField(choices=[('C', "User's waiver is currently up-to-date."), ('E', 'User must sign new waiver agreement.'), ('N', 'User has not signed a waiver.')], default='N', max_length=1)),
                ('waiver_time', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('A', 'User is the main active bike steward for their fleet.'), ('B', 'User is a designated back-up steward.'), ('I', 'User is no longer an active steward.'), ('N', 'User has never been a steward.')], default='N', max_length=1)),
                ('fleet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='fleet.Fleet')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='HistoricalEndUser',
            fields=[
                ('id', models.CharField(db_index=True, max_length=80)),
                ('waiver', models.CharField(choices=[('C', "User's waiver is currently up-to-date."), ('E', 'User must sign new waiver agreement.'), ('N', 'User has not signed a waiver.')], default='N', max_length=1)),
                ('waiver_time', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('A', 'User is the main active bike steward for their fleet.'), ('B', 'User is a designated back-up steward.'), ('I', 'User is no longer an active steward.'), ('N', 'User has never been a steward.')], default='N', max_length=1)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('fleet', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='fleet.Fleet')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical end user',
                'get_latest_by': 'history_date',
                'ordering': ('-history_date', '-history_id'),
            },
        ),
    ]
