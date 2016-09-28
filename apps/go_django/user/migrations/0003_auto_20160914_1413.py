# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-14 21:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_auto_20160914_1406'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enduser',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Organization'),
        ),
        migrations.AlterField(
            model_name='historicalenduser',
            name='organization',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='user.Organization'),
        ),
    ]