# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-20 23:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Geography',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('geo_id', models.IntegerField()),
                ('geography', models.CharField(max_length=255)),
                ('min_stop', models.CharField(max_length=3)),
                ('max_stop', models.CharField(max_length=3)),
            ],
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('code', models.CharField(max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='Stop',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stop_id', models.CharField(max_length=3)),
                ('name', models.CharField(default='Unnamed', max_length=64)),
                ('desc', models.TextField(blank=True, default='')),
                ('gps_ref', models.CharField(max_length=1)),
                ('lat', models.DecimalField(blank=True, decimal_places=6, max_digits=9)),
                ('lng', models.DecimalField(blank=True, decimal_places=6, max_digits=9)),
                ('signage', models.CharField(default='Undecided', max_length=20)),
                ('shelter', models.CharField(default='Undecided', max_length=20)),
                ('operating', models.DateField()),
                ('speed', models.IntegerField(default=25)),
                ('connections', models.TextField(blank=True, default='')),
                ('geography', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stop.Geography')),
            ],
        ),
        migrations.AddField(
            model_name='inventory',
            name='stop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stop.Stop'),
        ),
    ]
