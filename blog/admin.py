from django.contrib import admin
from .models import Article, Category, Tag, Login
# Register your models here.


class LoginAdmin(admin.ModelAdmin):
    model = Login

admin.site.register(Login, LoginAdmin)

class CategoryInline(admin.TabularInline):
    model = Category


class TagInline(admin.TabularInline):
    model = Tag


class ArticleAdmin(admin.ModelAdmin):
    inlines = [CategoryInline, TagInline]

    list_display = ['title', 'create_time']


admin.site.register(Article, ArticleAdmin)
