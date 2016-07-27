# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-27 17:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('route', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Holiday',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('holiday', models.DateField()),
            ],
        ),
        migrations.RenameField(
            model_name='stoptime',
            old_name='trip_id',
            new_name='trip',
        ),
        migrations.RemoveField(
            model_name='stoptime',
            name='direction',
        ),
        migrations.RemoveField(
            model_name='stoptime',
            name='driver',
        ),
        migrations.RemoveField(
            model_name='stoptime',
            name='joint',
        ),
        migrations.RemoveField(
            model_name='stoptime',
            name='route',
        ),
        migrations.AddField(
            model_name='trip',
            name='direction',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='route.Direction'),
            preserve_default=False,
        ),
    ]
