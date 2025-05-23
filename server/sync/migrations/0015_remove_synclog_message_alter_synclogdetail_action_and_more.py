# Generated by Django 5.1.7 on 2025-03-23 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sync', '0014_remove_synclog_detailed_logs_synclogdetail'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='synclog',
            name='message',
        ),
        migrations.AlterField(
            model_name='synclogdetail',
            name='action',
            field=models.CharField(choices=[('create', '创建'), ('update', '更新'), ('delete', '删除'), ('move', '移动'), ('info', '信息'), ('error', '错误')], max_length=20, verbose_name='操作类型'),
        ),
        migrations.AlterField(
            model_name='synclogdetail',
            name='object_type',
            field=models.CharField(choices=[('user', '用户'), ('department', '部门'), ('system', '系统消息')], max_length=20, verbose_name='对象类型'),
        ),
    ]
