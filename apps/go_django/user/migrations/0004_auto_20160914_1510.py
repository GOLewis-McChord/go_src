# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-14 22:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_auto_20160914_1413'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enduser',
            name='title_or_rank',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name='historicalenduser',
            name='title_or_rank',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
    ]