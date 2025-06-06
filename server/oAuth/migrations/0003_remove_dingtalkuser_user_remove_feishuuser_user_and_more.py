# Generated by Django 5.1.7 on 2025-03-24 05:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oAuth', '0002_dingtalkconfig_fetch_users_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dingtalkuser',
            name='user',
        ),
        migrations.RemoveField(
            model_name='feishuuser',
            name='user',
        ),
        migrations.RemoveField(
            model_name='wecomuser',
            name='user',
        ),
        migrations.AddField(
            model_name='user',
            name='dingtalk_user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='local_user', to='oAuth.dingtalkuser'),
        ),
        migrations.AddField(
            model_name='user',
            name='feishu_user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='local_user', to='oAuth.feishuuser'),
        ),
        migrations.AddField(
            model_name='user',
            name='gitee_user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='local_user', to='oAuth.giteeuser'),
        ),
        migrations.AddField(
            model_name='user',
            name='github_user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='local_user', to='oAuth.githubuser'),
        ),
        migrations.AddField(
            model_name='user',
            name='gitlab_user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='local_user', to='oAuth.gitlabuser'),
        ),
        migrations.AddField(
            model_name='user',
            name='google_user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='local_user', to='oAuth.googleuser'),
        ),
        migrations.AddField(
            model_name='user',
            name='wecom_user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='local_user', to='oAuth.wecomuser'),
        ),
        migrations.AlterField(
            model_name='giteeuser',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='gitee_user_link', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='githubuser',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='github_user_link', to=settings.AUTH_USER_MODEL, verbose_name='关联用户'),
        ),
        migrations.AlterField(
            model_name='gitlabuser',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='gitlab_user_link', to=settings.AUTH_USER_MODEL, verbose_name='关联用户'),
        ),
        migrations.AlterField(
            model_name='googleuser',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='google_user_link', to=settings.AUTH_USER_MODEL, verbose_name='关联用户'),
        ),
    ]
