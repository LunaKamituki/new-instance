import json
import requests
import urllib.parse
import time
import datetime
import random
import os
import subprocess
from cache import cache
import ast

# 3 => (3.0, 1.5)
max_api_wait_time = (3.0, 1.5)
# 10 => 10
max_time = 10

class InvidiousAPI:
    def __init__(self):
        self.videos_api = ast.literal_eval(requests.get('https://raw.githubusercontent.com/LunaKamituki/yukiyoutube-inv-instances/main/instances.txt').text)
        
        self.channels_api = []
        self.comments_api = []
        
        [[self.channels_api.append(api), self.comments_api.append(api)] for api in self.videos_api]

    def __repr__(self):
        return {
            'videos_api': self.videos_api,
            'channels_api': self.channels_api,
            'comments_api': self.comments_api
        }

        
invidious_api = InvidiousAPI()

url = requests.get('https://raw.githubusercontent.com/mochidukiyukimi/yuki-youtube-instance/main/instance.txt').text.rstrip()

version = "1.0"

os.system("chmod 777 ./yukiverify")

class APItimeoutError(Exception):
    pass

def is_json(json_str):
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError as jde:
        pass
    return False

def updateList(list, str):
    list.append(str)
    list.remove(str)
    return list

def apirequest(api_urlpath, api_urls):
    starttime = time.time()
    
    for api in api_urls:
        if  time.time() - starttime >= max_time - 1:
            break
            
        try:
            res = requests.get(api + 'api/v1' + api_urlpath, timeout=max_api_wait_time)
            if res.status_code == 200 and is_json(res.text):
                return res.text
            else:
                print(f"エラー: {api}")
                updateList(api_urls, api)
        except:
            print(f"タイムアウト: {api}")
            updateList(api_urls, api)
    
    raise APItimeoutError("APIがタイムアウトしました")

def get_info(request):
    return json.dumps([version, os.environ.get('RENDER_EXTERNAL_URL'), str(request.scope["headers"]), str(request.scope['router'])[39:-2]])

def get_data(videoid):
    t = json.loads(apirequest(f"/videos/{urllib.parse.quote(videoid)}", invidious_api.videos_api))
    return [{"id": i["videoId"], "title": i["title"], "authorId": i["authorId"], "author": i["author"]} for i in t["recommendedVideos"]], list(reversed([i["url"] for i in t["formatStreams"]]))[:2], t["descriptionHtml"].replace("\n", "<br>"), t["title"], t["authorId"], t["author"], t["authorThumbnails"][-1]["url"]

def get_search(q, page):
    t = json.loads(apirequest(f"/search?q={urllib.parse.quote(q)}&page={page}&hl=jp", invidious_api.videos_api))

    def load_search(i):
        if i["type"] == "video":
            return {"title": i["title"], "id": i["videoId"], "authorId": i["authorId"], "author": i["author"], "length":str(datetime.timedelta(seconds=i["lengthSeconds"])), "published": i["publishedText"], "type": "video"}
            
        elif i["type"] == "playlist":
            return {"title": i["title"], "id": i["playlistId"], "thumbnail": i["videos"][0]["videoId"], "count": i["videoCount"], "type": "playlist"}
            
        elif i["authorThumbnails"][-1]["url"].startswith("https"):
            return {"author": i["author"], "id": i["authorId"], "thumbnail": i["authorThumbnails"][-1]["url"], "type": "channel"}
            
        else:
            return {"author": i["author"], "id": i["authorId"], "thumbnail": f"https://{i['authorThumbnails'][-1]['url']}", "type": "channel"}
    
    return [load_search(i) for i in t]

def get_channel(channelid):
    t = json.loads(apirequest(f"/channels/{urllib.parse.quote(channelid)}", invidious_api.channels_api))
    if t["latestVideos"] == []:
        print("APIがチャンネルを返しませんでした")
        apichannels = updateList(apichannels, apichannels[0])
        raise APItimeoutError("APIがチャンネルを返しませんでした")
    return [[{"title": i["title"], "id": i["videoId"], "authorId": t["authorId"], "author": t["author"], "published": i["publishedText"], "type":"video"} for i in t["latestVideos"]], {"channelname": t["author"], "channelicon": t["authorThumbnails"][-1]["url"], "channelprofile": t["descriptionHtml"]}]

def get_playlist(listid, page):
    t = json.loads(apirequest(f"/playlists/{urllib.parse.quote(listid)}?page={urllib.parse.quote(page)}", invidious_api.videos_api))["videos"]
    return [{"title": i["title"], "id": i["videoId"], "authorId": i["authorId"], "author": i["author"], "type": "video"} for i in t]

def get_comments(videoid):
    t = json.loads(apirequest(f"/comments/{urllib.parse.quote(videoid)}?hl=jp", invidious_api.comments_api))["comments"]
    return [{"author": i["author"], "authoricon": i["authorThumbnails"][-1]["url"], "authorid": i["authorId"], "body": i["contentHtml"].replace("\n", "<br>")} for i in t]

'''
使われていないし戻り値も設定されていないためコメントアウト
def get_replies(videoid, key):
    t = json.loads(apirequest(f"/comments/{videoid}?hmac_key={key}&hl=jp&format=html", invidious_api.comments_api))["contentHtml"]
'''

def check_cokie(cookie):
    print(cookie)
    if cookie == "True":
        return True
    return False

def get_verifycode():
    try:
        result = subprocess.run(["./yukiverify"], encoding='utf-8', stdout=subprocess.PIPE)
        hashed_password = result.stdout.strip()
        return hashed_password
    except subprocess.CalledProcessError as e:
        print(f"get_verifycode__Error: {e}")
        return None



from fastapi import FastAPI, Depends
from fastapi import Response, Cookie, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.responses import RedirectResponse as redirect
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Union


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/css", StaticFiles(directory="./css"), name="static")
app.mount("/word", StaticFiles(directory="./blog", html=True), name="static")
app.add_middleware(GZipMiddleware, minimum_size=1000)

from fastapi.templating import Jinja2Templates
template = Jinja2Templates(directory='templates').TemplateResponse

no_robot_meta_tag = '<meta name="robots" content="noindex,nofollow">'

@app.get("/", response_class=HTMLResponse)
def home(response: Response, request: Request, yuki: Union[str] = Cookie(None)):
    if check_cokie(yuki):
        response.set_cookie("yuki", "True", max_age=60 * 60 * 24 * 7)
        return template("home.html", {"request": request})
    print(check_cokie(yuki))
    return redirect("/word")


@app.get('/watch', response_class=HTMLResponse)
def video(v:str, response: Response, request: Request, yuki: Union[str] = Cookie(None), proxy: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    response.set_cookie(key="yuki", value="True", max_age=7*24*60*60)
    videoid = v
    t = get_data(videoid)
    response.set_cookie("yuki", "True", max_age=60 * 60 * 24 * 7)
    return template('video.html', {"request": request, "videoid":videoid, "videourls":t[1], "res":t[0], "description":t[2], "videotitle":t[3], "authorid":t[4], "authoricon":t[6], "author":t[5], "proxy":proxy})

@app.get("/search", response_class=HTMLResponse,)
def search(q:str, response: Response, request: Request, page:Union[int, None]=1, yuki: Union[str] = Cookie(None), proxy: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    response.set_cookie("yuki", "True", max_age=60 * 60 * 24 * 7)
    return template("search.html", {"request": request, "results":get_search(q, page), "word":q, "next":f"/search?q={q}&page={page + 1}", "proxy":proxy})

@app.get("/hashtag/{tag}")
def search(tag:str, response: Response, request: Request, page:Union[int, None]=1, yuki: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    return redirect(f"/search?q={tag}")

@app.get("/channel/{channelid}", response_class=HTMLResponse)
def channel(channelid:str, response: Response, request: Request, yuki: Union[str] = Cookie(None), proxy: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    response.set_cookie("yuki", "True", max_age=60 * 60 * 24 * 7)
    t = get_channel(channelid)
    return template("channel.html", {"request": request, "results": t[0], "channelname": t[1]["channelname"], "channelicon": t[1]["channelicon"], "channelprofile": t[1]["channelprofile"], "proxy": proxy})

@app.get("/playlist", response_class=HTMLResponse)
def playlist(list:str, response: Response, request: Request, page:Union[int, None]=1, yuki: Union[str] = Cookie(None), proxy: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    response.set_cookie("yuki", "True", max_age=60 * 60 * 24 * 7)
    return template("search.html", {"request": request, "results": get_playlist(list, str(page)), "word": "", "next": f"/playlist?list={list}", "proxy": proxy})

@app.get("/comments")
def comments(request: Request, v:str):
    return template("comments.html", {"request": request, "comments": get_comments(v)})

@app.get("/thumbnail")
def thumbnail(v:str):
    return Response(content = requests.get(f"https://img.youtube.com/vi/{v}/0.jpg").content, media_type=r"image/jpeg")

@app.get("/suggest")
def suggest(keyword:str):
    return [i[0] for i in json.loads(requests.get("http://www.google.com/complete/search?client=youtube&hl=ja&ds=yt&q=" + urllib.parse.quote(keyword)).text[19:-1])[1]]


@cache(seconds=60)
def getSource(name):
    return requests.get(f'https://raw.githubusercontent.com/LunaKamituki/yuki-source/main/{name}.html').text

@app.get("/bbs", response_class=HTMLResponse)
def view_bbs(request: Request, name: Union[str, None] = "", seed:Union[str, None]="", channel:Union[str, None]="main", verify:Union[str, None]="false", yuki: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    res = HTMLResponse(no_robot_meta_tag + requests.get(f"{url}bbs?name={urllib.parse.quote(name)}&seed={urllib.parse.quote(seed)}&channel={urllib.parse.quote(channel)}&verify={urllib.parse.quote(verify)}", cookies={"yuki":"True"}).text.replace('AutoLink(xhr.responseText);', 'urlConvertToLink(xhr.responseText);') + getSource('bbs_1') + getSource('shortcut_help') + getSource('bbs_2') + getSource('bbs_5'))
    return res

@cache(seconds=5)
def bbsapi_cached(verify, channel):
    return requests.get(f"{url}bbs/api?t={urllib.parse.quote(str(int(time.time()*1000)))}&verify={urllib.parse.quote(verify)}&channel={urllib.parse.quote(channel)}", cookies={"yuki":"True"}).text

@app.get("/bbs/api", response_class=HTMLResponse)
def view_bbs(request: Request, t: str, channel:Union[str, None]="main", verify: Union[str, None] = "false"):
    # print(f"{url}bbs/api?t={urllib.parse.quote(t)}&verify={urllib.parse.quote(verify)}&channel={urllib.parse.quote(channel)}")
    return bbsapi_cached(verify, channel)

@app.get("/bbs/result")
def write_bbs(request: Request, name: str = "", message: str = "", seed:Union[str, None] = "", channel:Union[str, None]="main", verify:Union[str, None]="false", yuki: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    t = requests.get(f"{url}bbs/result?name={urllib.parse.quote(name)}&message={urllib.parse.quote(message)}&seed={urllib.parse.quote(seed)}&channel={urllib.parse.quote(channel)}&verify={urllib.parse.quote(verify)}&info={urllib.parse.quote(get_info(request))}&serververify={get_verifycode()}", cookies={"yuki":"True"}, allow_redirects=False)
    if t.status_code != 307:
        return HTMLResponse(no_robot_meta_tag + t.text.replace('AutoLink(xhr.responseText);', 'urlConvertToLink(xhr.responseText);') + getSource('bbs_1') + getSource('shortcut_help') + getSource('bbs_2') + getSource('bbs_5'))
        
    return redirect(f"/bbs?name={urllib.parse.quote(name)}&seed={urllib.parse.quote(seed)}&channel={urllib.parse.quote(channel)}&verify={urllib.parse.quote(verify)}")

@cache(seconds=60)
def how_cached():
    return requests.get(f"{url}bbs/how").text

@app.get("/bbs/how", response_class=PlainTextResponse)
def view_commonds(request: Request, yuki: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    return no_robot_meta_tag + how_cached()

@app.get("/info", response_class=HTMLResponse)
def viewlist(response: Response, request: Request, yuki: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    response.set_cookie("yuki", "True", max_age=60 * 60 * 24 * 7)
    
    return template("info.html", {"request": request, "Youtube_API": invidious_api.videos_api[0], "Channel_API": invidious_api.channels_api[0], "Comments_API": invidious_api.comments_api[0]})

@app.get("/load_instance")
def home():
    global url, invidious_api
    url = requests.get('https://raw.githubusercontent.com/mochidukiyukimi/yuki-youtube-instance/main/instance.txt').text.rstrip()
    invidious_api = InvidiousAPI()

@app.exception_handler(500)
def page(request: Request, __):
    return template("APIwait.html", {"request": request}, status_code=500)

@app.exception_handler(APItimeoutError)
def APIwait(request: Request, exception: APItimeoutError):
    return template("APIwait.html", {"request": request}, status_code=500)
