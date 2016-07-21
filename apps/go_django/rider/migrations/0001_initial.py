# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-20 23:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('stop', '0001_initial'),
        ('vehicle', '0001_initial'),
        ('driver', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Data',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.TimeField()),
                ('count', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Metadata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('sheet', models.CharField(max_length=4)),
                ('route', models.CharField(max_length=20)),
                ('login', models.DateTimeField()),
                ('start_mileage', models.IntegerField()),
                ('end_mileage', models.IntegerField()),
                ('logout', models.DateTimeField()),
                ('driver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='driver.Driver')),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vehicle.Vehicle')),
            ],
        ),
        migrations.AddField(
            model_name='data',
            name='metadata',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rider.Metadata'),
        ),
        migrations.AddField(
            model_name='data',
            name='off',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='off_stop', to='stop.Stop'),
        ),
        migrations.AddField(
            model_name='data',
            name='on',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='on_stop', to='stop.Stop'),
        ),
    ]
