from rest_framework import serializers
from django.contrib.auth.models import Group
from .models import User, WeComConfig, FeiShuConfig, DingTalkConfig, GitHubConfig, GitHubUser, OAuthConfig, GoogleConfig, GoogleUser, GitLabConfig, GitLabUser, GiteeConfig, GiteeUser
from django.contrib.auth.hashers import make_password

class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='get_full_name', read_only=True)
    class Meta:
        model = User
        fields = [
            'id', 'username', 'name', 'first_name', 'last_name', 'avatar',
            'email', 'role', 'is_active', 'last_active_at', 
            'date_joined', 'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'last_active_at': {'read_only': True},
            'date_joined': {'read_only': True}
        }

    def create(self, validated_data):
        # 确保密码被正确加密
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # 更新时如果有密码，确保密码被加密
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField() 

class WeComConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeComConfig
        fields = ['id', 'corp_id', 'agent_id', 'secret', 'redirect_uri', 'enabled', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class FeiShuConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeiShuConfig
        fields = ['id', 'app_id', 'app_secret', 'redirect_uri', 'enabled', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class DingTalkConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DingTalkConfig
        fields = ['id', 'app_id', 'client_id', 'client_secret', 'redirect_uri', 'enabled', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class GitHubConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubConfig
        fields = ['id', 'client_id', 'client_secret', 'redirect_uri', 'enabled', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class GitHubUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubUser
        fields = ['id', 'github_id', 'login', 'name', 'email', 'avatar_url', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class GoogleConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleConfig
        fields = ['id', 'client_id', 'client_secret', 'redirect_uri', 'enabled', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class GoogleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleUser
        fields = ['id', 'google_id', 'email', 'name', 'given_name', 'family_name', 'picture', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class GitLabConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitLabConfig
        fields = '__all__'

class GitLabUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitLabUser
        fields = '__all__'

class GiteeConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiteeConfig
        fields = '__all__'

class GiteeUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiteeUser
        fields = '__all__'
