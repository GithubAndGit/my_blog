from rest_framework import serializers
from .models import Article, Login


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        # 可以之填充我们使用到的字段
        fields = ("title", "text", "url", "create_time")


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = Login
        fields = ("username", "password")
