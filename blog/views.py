import pymysql
# import self as self
# from aiohttp import request
from django.shortcuts import render, HttpResponse, redirect, HttpResponseRedirect
from django.views.generic import TemplateView
from django.http.response import JsonResponse
from django.core import serializers
from django.core.cache import cache
from django.db import transaction
from .models import Article, Category, Tag, Login
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate
from .serializers import ArticleSerializer
import time
import json, ujson
import math
import markdown
from concurrent.futures import ThreadPoolExecutor
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.views import APIView


def monkey_patch_json():
    json.__name__ = 'ujson'
    # json.dumps = ujson.dumps
    json.loads = ujson.loads


monkey_patch_json()


# Create your views here.


class LoginView():

    def __init__(self):
        self.POST = None
        self.method = None

    # 用户登录
    def login(request):
        if request.method == 'POST' and request.POST:  # post请求就是向服务端发送数据验证密码是否正确
            username = request.POST.get("username")
            password = request.POST.get("password")
            e = Login.objects.filter(username=username).first()  # 向数据库请求数据username, 获取第一条数据, 如果第一条数据不是, 则找下一条。
            if e:  # 如果e在数据库中存在
                now_password = password
                db_password = e.password  # e在数据库中的password赋值给db_password
                if now_password == db_password:
                    # 转账的业务逻辑有问题，我们需要添加再次验证
                    # user_sms_code = request.POST.get('sms_code')
                    # server_sms_code = redis.get('sms_code')
                    # 黑客是获取不到短信验证码的
                    # user_sms_code = '1234'
                    # server_sms_code = '1234'
                    # if user_sms_code != server_sms_code:
                    #     return HttpResponse('哥们你找削呢，敢转我的账，你不知道验证码吧')
                    response = HttpResponseRedirect('/myblog/')
                    response.set_cookie("username", e.username)  # 设置网页上的cookie
                    return response
                else:
                    context = {
                        "error": "您输入的密码错误, 请重新输入!"
                    }
                    return render(request, "login.html", context)
            else:
                context = {
                    "error": "您输入的用户名错误, 请重新输入!"
                }
                return render(request, "login.html", context)
        return render(request, "login.html")


class RegisterView():
    def __init__(self):
        self.method = None
        self.GET = None

    def register(request):
        if request.method == "GET" and request.GET:
            username = request.GET.get("username")
            password = request.GET.get("password")
            person = Login.objects.filter(username=username)  # 查找所有的username是否有当前的username
            if any(person):  # 可迭代对象person中有一个是True则是True
                return HttpResponse("您输入的用户名已存在！")
            else:
                Login.objects.create(
                    username=username,
                    password=password,
                )
                return HttpResponseRedirect('/')
        return render(request, "register.html")


class IndexView(TemplateView):
    template_name = "index.html"

    def get(self, *args, **kwargs):
        article_list = Article.objects.order_by("-create_time")  # 根据创建时间得到Article, 将Article赋值给article_list
        for article in article_list:  # 遍历 article_list
            article.pub_date = article.create_time.strftime("%m-%d").replace("-", "月")
            article.length = len(article.text)
            article.read_time = math.ceil(len(article.text) / 180) if article.text else 0
            # 外键可以通过以下方式获取到集合
            article.categories = article.category_set.values()
            article.tags = article.tag_set.values()
            # cate_list = Category.objects.filter(article_id=article.ic)

        context = {
            "article_list": article_list,
        }

        return self.render_to_response(context)


class DetailView(TemplateView):
    template_name = "new_detail.html"

    def get(self, request, *args, **kwargs):
        article = Article.objects.get(url=request.path)
        content = ""
        for line in article.text.split("\n"):
            content += line.strip("  ") + "\n" if "```" in line else line.strip("#") + '\n'
            content += "\n"
        article.content = markdown.markdown(content, extensions=[
            'markdown.extensions.extra',  # 转换标题, 字体等
            'markdown.extensions.codehilite',  # 添加高亮功能
            'markdown.extensions.toc',  # 将表单渲染为html document类型
        ])

        # article.id + 1 是最快的方案, 但是我们不能保证自增键id不会中断.
        # 当前返回的结果不是QuerySet而是RawQuerySet, 当前并没有真正地请求并获取到查询结果.
        raw_query_set = Article.objects.raw(
            f"select * from {Article._meta.db_table} where id < {article.id} order by id desc limit 1")
        try:
            next_article = raw_query_set[0]
            context = {
                "next_article": next_article,
                "article": article,
            }
        except IndexError:
            context = {
                "article": article,
            }
        return self.render_to_response(context)


class ArchiveView(TemplateView):
    """
    archive_dict = { "2018": {"year": 2018, "article_list": []}}
    """
    template_name = "archive.html"

    def get(self, request, *args, **kwargs):
        global context
        redis_key = "archive_cache"
        redis_value = cache.get(redis_key)
        if redis_value:
            print("hit cache")
            serializers_archives = json.loads(redis_value)
            archive_list = []

            article_count = 0
            for archive in serializers_archives:
                # 为了模板可以正常渲染, 需要将article反序列化为对象
                archive_list.append({
                    "year": archive['year'],
                    "article_list": [obj.object for obj in serializers.deserialize('json', archive['article_list'])]
                })
                article_count += len(archive_list)

                context = {
                    "archive_list": archive_list,
                    "article_count": article_count
                }
        else:

            article_list = Article.objects.all()

            archive_dict = {}
            for article in article_list:
                year = article.create_time.strftime("%Y")
                # 如果当前字典没有目标key, 则给定默认值
                # 如果当前字典有目标key, 则无变化
                archive_dict.setdefault(year, {"year": year, "article_list": []})
                archive_dict[year]['article_list'].append(article)

            context = {
                "archive_list": archive_dict.values(),
                "article_count": len(article_list)
            }

            # 缓存archive_list
            serializer_archives = []
            for archive in archive_dict.values():
                serializer_archives.append({
                    "year": archive['year'],
                    "article_list": serializers.serialize("json", archive['article_list'])
                })
            cache.set(redis_key, json.dumps(serializer_archives))
            cache.expire(redis_key, 30)

        return self.render_to_response(context)


class ArticleApiView(APIView):

    def get(self, request, *args, **kwargs):
        """
        article?limit_num=2
        :param args:
        :param kwargs:
        :return:
        """
        # 重点是学习如何获取url当中的参数
        limit_num = request.GET.get("limit_num", None)
        if limit_num:
            article_array = Article.objects.all()[:int(limit_num)]
        else:
            article_array = Article.objects.all()
        se_article_array = ArticleSerializer(article_array, many=True)
        return JsonResponse({
            "static": 200,
            "data": se_article_array.data
        }, safe=False)

    def post(self, request, *args, **kwargs):
        """
        添加文章的时候，需要带上category 和tag的信息
        只要article, category, tay有一方报错的时候, 当前文章都算添加失败。
        所以我们应该适用事务进行包装
        :param args:
        :param kwargs:
        :return:
        """
        try:
            message = {"status": 200}
            with transaction.atomic():
                title = request.POST['title']
                text = request.POST['text']
                categories = json.loads(request.POST['categories'])
                tags = json.loads(request.POST['tags'])

                print(type(categories), type(categories[0]))

                article_data = {
                    "title": title,
                    "text": text,
                    "url": f"/{time.strftime('%Y/%m/%d')}/{title}.html"
                }
                se_article = ArticleSerializer(data=article_data)
                se_article.is_valid()
                article = se_article.create(se_article.data)
                article.save()

                for category in categories:
                    cate = Category(
                        name=category['name'],
                        slug=category['slug'],
                        uri=f"/categories/{category['slug']}/"
                    )
                    cate.article = article
                    cate.save()

                for tag in tags:
                    tag = Tag(
                        name=tag['name'],
                        slug=tag['slug'],
                        uri=f"/tags/{tag['slug']}/"
                    )
                    tag.article = article
                    tag.save()

        except:
            message = {"status": 500, "reason": "添加文章失败"}
        finally:
            response = JsonResponse(message, safe=False)
            response['Access-Control-Allow-Origin'] = "*"  # *表示任意域名
            response['Access-Control-Allow-Headers'] = "*"  # *表示任意域名
            response['Access-Control-Allow-Methods'] = "OPTIONS, POST, GET"  # *表示任意域名
            return response

    def put(self, request, *args, **kwargs):
        """
        重点是如何获取携带的参数
        request.POST(key)
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        pass

    def delete(self, *args, **kwargs):
        pass


if __name__ == '__main__':
    with ThreadPoolExecutor(61) as t:
        for i in range(100):
            t.submit(LoginView)
            t.submit(RegisterView)
            t.submit(IndexView)
            t.submit(DetailView)
            t.submit(Article)
            t.submit(ArchiveView)
