import hashlib

from django.db import models
from mdeditor.fields import MDTextField

# Create your models here.


class Login(models.Model):
    objects = None
    username = models.CharField(max_length=32, unique=True, null=True)
    password = models.CharField(max_length=40)

    class Meta:
        db_table = "login"

    def __str__(self):
        return self.username

    @classmethod
    def encrypt_password(cls, password):
        """使用SHA-1加密密码，返回长度为40的加密后的字符串。"""
        return hashlib.sha1(password.encode()).hexdigest()


class Article(models.Model):
    objects = None
    title = models.CharField(max_length=200)
    text = MDTextField()
    url = models.CharField(max_length=200)
    update_time = models.DateTimeField(auto_now=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "article"

    def __str__(self):
        return f"<Article {self.title}>"


class Category(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)  # 建立外键与主表链接，主表删除数据，从表也删除
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=200)
    uri = models.CharField(max_length=200)

    class Meta:
        db_table = "category"

class Tag(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=200)
    uri = models.CharField(max_length=200)

    class Meta:
        db_table = "tag"

