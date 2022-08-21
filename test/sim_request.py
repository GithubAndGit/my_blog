import requests
import json

def article_post():
    url = "http://127.0.0.1:8000/api/article/"
    data = {
        'title': "test_title_2",
        "text": "test_text_2",
        "categories": json.dumps([{"name": "blog", "slug": "blog"}]),
        "tags": json.dumps([{"name": "blog", "slug": "blog"}])
    }
    result = requests.post(url=url, data=data)
    print(result.text)


article_post()
