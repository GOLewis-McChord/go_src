# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-14 21:06
from __future__ import unicode_literals

from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('name', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='enduser',
            name='cell_phone',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='enduser',
            name='mailing_address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='enduser',
            name='office_phone',
            field=phonenumber_field.modelfields.PhoneNumberField(default='+12539663939'),
        ),
        migrations.AddField(
            model_name='enduser',
            name='organization',
            field=models.CharField(default='Unknown', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='enduser',
            name='role_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='enduser',
            name='title_or_rank',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='historicalenduser',
            name='cell_phone',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalenduser',
            name='mailing_address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='historicalenduser',
            name='office_phone',
            field=phonenumber_field.modelfields.PhoneNumberField(default='+12539663939'),
        ),
        migrations.AddField(
            model_name='historicalenduser',
            name='organization',
            field=models.CharField(default='Unknown', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalenduser',
            name='role_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalenduser',
            name='title_or_rank',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
    ]