# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-08-22 07:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mysite', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InfoBody',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('startDate', models.DateTimeField(auto_now_add=True, verbose_name='填写日期')),
                ('body', models.TextField(max_length=600, verbose_name='详细内容')),
            ],
            options={
                'ordering': ('-startDate',),
            },
        ),
        migrations.CreateModel(
            name='InfoPublic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('startDate', models.DateTimeField(auto_now_add=True, verbose_name='填写日期')),
                ('title', models.CharField(max_length=50, verbose_name='标题')),
            ],
            options={
                'ordering': ('-startDate',),
            },
        ),
        migrations.AlterModelOptions(
            name='worklog',
            options={'ordering': ('-date', 'id')},
        ),
        migrations.AddField(
            model_name='tradingaccount',
            name='creationTime',
            field=models.CharField(blank=True, max_length=12, null=True, verbose_name='创建时间'),
        ),
        migrations.AddField(
            model_name='tradingaccount',
            name='enabled',
            field=models.IntegerField(choices=[[0, '未启用'], [1, '启用']], default=1, verbose_name='状态'),
        ),
        migrations.AddField(
            model_name='tradingaccount',
            name='password',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='密码'),
        ),
        migrations.AlterField(
            model_name='simulationaccount',
            name='host',
            field=models.CharField(max_length=20, unique=True, verbose_name='交易账号'),
        ),
        migrations.AlterField(
            model_name='tradingaccount',
            name='appid',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='ApppID'),
        ),
        migrations.AlterField(
            model_name='tradingaccount',
            name='host',
            field=models.CharField(max_length=40, verbose_name='用户名'),
        ),
        migrations.AlterField(
            model_name='tradingaccount',
            name='license',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='许可证'),
        ),
        migrations.AlterField(
            model_name='tradingaccount',
            name='port',
            field=models.IntegerField(blank=True, null=True, verbose_name='端口'),
        ),
        migrations.AlterField(
            model_name='tradingaccount',
            name='userid',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='用户ID'),
        ),
        migrations.AlterField(
            model_name='users',
            name='name',
            field=models.CharField(max_length=10, unique=True, verbose_name='用户名'),
        ),
        migrations.AddField(
            model_name='infopublic',
            name='belonged',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mysite.Users', verbose_name='所属用户'),
        ),
        migrations.AddField(
            model_name='infobody',
            name='belonged',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mysite.Users', verbose_name='所属用户'),
        ),
        migrations.AddField(
            model_name='infobody',
            name='belongedTitle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mysite.InfoPublic', verbose_name='所属话题'),
        ),
    ]
