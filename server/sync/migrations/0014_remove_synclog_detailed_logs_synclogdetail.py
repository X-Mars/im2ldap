# Generated by Django 5.1.7 on 2025-03-23 10:56

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sync', '0013_synclog_detailed_logs'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='synclog',
            name='detailed_logs',
        ),
        migrations.CreateModel(
            name='SyncLogDetail',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('object_type', models.CharField(choices=[('user', '用户'), ('department', '部门')], max_length=20, verbose_name='对象类型')),
                ('action', models.CharField(choices=[('create', '创建'), ('update', '更新'), ('delete', '删除'), ('move', '移动')], max_length=20, verbose_name='操作类型')),
                ('object_id', models.CharField(max_length=255, verbose_name='对象ID')),
                ('object_name', models.CharField(max_length=255, verbose_name='对象名称')),
                ('old_data', models.JSONField(blank=True, null=True, verbose_name='原数据')),
                ('new_data', models.JSONField(blank=True, null=True, verbose_name='新数据')),
                ('details', models.TextField(blank=True, verbose_name='详情描述')),
                ('sync_log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='details', to='sync.synclog', verbose_name='所属同步日志')),
            ],
            options={
                'verbose_name': '同步日志详情',
                'verbose_name_plural': '同步日志详情',
                'ordering': ['object_type', 'action', 'object_name'],
            },
        ),
    ]
