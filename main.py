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


header = {
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15'
}

class InvidiousAPI:
    def __init__(self):
        self.all = ast.literal_eval(requests.get('https://raw.githubusercontent.com/LunaKamituki/yukiyoutube-inv-instances/refs/heads/main/main.txt', headers=header, timeout=(1.0, 0.5)).text)
        
        self.video = self.all['video']
        self.playlist = self.all['playlist']
        self.search = self.all['search']
        self.channel = self.all['channel']
        self.comments = self.all['comments']

        self.check_video = False

    def info(self):
        return {
            'API': self.all,
            'checkVideo': self.check_video
        }

        
invidious_api = InvidiousAPI()

url = requests.get('https://raw.githubusercontent.com/mochidukiyukimi/yuki-youtube-instance/refs/heads/main/instance.txt', headers=header).text.rstrip()

version = "1.0"
new_instance_version = "1.3.2"


os.system("chmod 777 ./yukiverify")

class APITimeoutError(Exception):
    pass

class UnallowedBot(Exception):
    pass

def isJSON(json_str):
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

def requestAPI(path, api_urls):
    starttime = time.time()
    
    for api in api_urls:
        if  time.time() - starttime >= max_time - 1:
            break
            
        try:
            print(api + 'api/v1' + path)
            res = requests.get(api + 'api/v1' + path, headers=header, timeout=max_api_wait_time)
            if res.status_code == requests.codes.ok and isJSON(res.text):
                
                if invidious_api.check_video and path.startswith('/video/'):
                    # 動画の有無をチェックする場合
                    video_res = requests.get(json.loads(res.text)['formatStreams'][0]['url'], headers=header, timeout=(3.0, 0.5))
                    if not 'video' in video_res.headers['Content-Type']:
                        print(f"No Video(True)({video_res.headers['Content-Type']}): {api}")
                        updateList(api_urls, api)
                        continue

                if path.startswith('/channel/') and json.loads(res.text)["latestvideo"] == []:
                    print(f"No Channel: {api}")
                    updateList(api_urls, api)
                    continue

                print(f"Success({invidious_api.check_video})({path.split('/')[1].split('?')[0]}): {api}")
                return res.text

            elif isJSON(res.text):
                # ステータスコードが200ではないかつ内容がJSON形式の場合
                print(f"Returned Err0r(JSON): {api} ('{json.loads(res.text)['error'].replace('error', 'err0r')}')")
                updateList(api_urls, api)
            else:
                # ステータスコードが200ではないかつ内容がJSON形式ではない場合
                print(f"Returned Err0r: {api} ('{res.text}')")
                updateList(api_urls, api)
        except:
            # 例外等が発生した場合
            print(f"Err0r: {api}")
            updateList(api_urls, api)
    
    raise APITimeoutError("APIがタイムアウトしました")


def getInfo(request):
    return json.dumps([version, os.environ.get('RENDER_EXTERNAL_URL'), str(request.scope["headers"]), str(request.scope['router'])[39:-2]])

failed = "Load Failed"

def getVideoData(videoid):
    t = json.loads(requestAPI(f"/videos/{urllib.parse.quote(videoid)}", invidious_api.video))

    if 'recommendedvideo' in t:
        recommended_videos = t["recommendedvideo"]
    elif 'recommendedVideos' in t:
        recommended_videos = t["recommendedVideos"]
    else:
        recommended_videos = {
            "videoId": failed,
            "title": failed,
            "authorId": failed,
            "author": failed,
            "lengthSeconds": 0,
            "viewCountText": "Load Failed"
        }

    return [
        {
            'video_urls': list(reversed([i["url"] for i in t["formatStreams"]]))[:2],
            'description_html': t["descriptionHtml"].replace("\n", "<br>"),
            'title': t["title"],
            'length_text': str(datetime.timedelta(seconds=t["lengthSeconds"])),
            'author_id': t["authorId"],
            'author': t["author"],
            'author_thumbnails_url': t["authorThumbnails"][-1]["url"],
            'view_count': t["viewCount"],
            'like_count': t["likeCount"],
            'subscribers_count': t["subCountText"]
        },
        [
            {
                "video_id": i["videoId"],
                "title": i["title"],
                "author_id": i["authorId"],
                "author": i["author"],
                "length_text": str(datetime.timedelta(seconds=i["lengthSeconds"])),
                "view_count_text": i["viewCountText"]
            } for i in recommended_videos
        ]
    ]

def getSearchData(q, page):

    def formatSearchData(data_dict):
        if data_dict["type"] == "video":
            return {
                "type": "video",
                "title": data_dict["title"] if 'title' in data_dict else failed,
                "id": data_dict["videoId"] if 'videoId' in data_dict else failed,
                "authorId": data_dict["authorId"] if 'authorId' in data_dict else failed,
                "author": data_dict["author"] if 'author' in data_dict else failed,
                "published": data_dict["publishedText"] if 'publishedText' in data_dict else failed,
                "length": str(datetime.timedelta(seconds=data_dict["lengthSeconds"])),
                "view_count_text": data_dict["viewCountText"]
            }
            
        elif data_dict["type"] == "playlist":
            return {
                    "type": "playlist",
                    "title": data_dict["title"] if 'title' in data_dict else failed,
                    "id": data_dict['playlistId'] if 'playlistId' in data_dict else failed,
                    "thumbnail": data_dict["playlistThumbnail"] if 'playlistThumbnail' in data_dict else failed,
                    "count": data_dict["videoCount"] if 'videoCount' in data_dict else failed
                }
            
        elif data_dict["authorThumbnails"][-1]["url"].startswith("https"):
            return {
                "type": "channel",
                "author": data_dict["author"] if 'author' in data_dict else failed,
                "id": data_dict["authorId"] if 'authorId' in data_dict else failed,
                "thumbnail": data_dict["authorThumbnails"][-1]["url"] if 'authorThumbnails' in data_dict and len(data_dict["authorThumbnails"]) and 'url' in data_dict["authorThumbnails"][-1] else failed
            }
        else:
            return {
                "type": "channel",
                "author": data_dict["author"] if 'author' in data_dict else failed,
                "id": data_dict["authorId"] if 'authorId' in data_dict else failed,
                "thumbnail": "https://" + data_dict['authorThumbnails'][-1]['url']
            }

    # "datas"というのは気持ち悪いかもしれないが、複数のデータが入っていると明示できるという
    # メリットの方がコードを書く上では大きい
    datas_dict = json.loads(requestAPI(f"/search?q={urllib.parse.quote(q)}&page={page}&hl=jp", invidious_api.search))
    return [formatSearchData(data_dict) for data_dict in datas_dict]


def getChannelData(channelid):
    t = json.loads(requestAPI(f"/channels/{urllib.parse.quote(channelid)}", invidious_api.channel))
    if 'latestvideo' in t:
        latest_videos = t['latestvideo']
    elif 'latestVideos' in t:
        latest_videos = t['latestVideos']
    else:
        latest_videos = {
            "title": failed,
            "videoId": failed,
            "authorId": failed,
            "author": failed,
            "publishedText": failed,
            "viewCountText": "0",
            "lengthSeconds": "0"
        }
    
    
    return [
        [
            {
                # 直近の動画
                "type":"video",
                "title": i["title"],
                "id": i["videoId"],
                "authorId": t["authorId"],
                "author": t["author"],
                "published": i["publishedText"],
                "view_count_text": i['viewCountText'],
                "length_str": str(datetime.timedelta(seconds=i["lengthSeconds"]))
            } for i in latest_videos
        ], {
            # チャンネル情報
            "channel_name": t["author"],
            "channel_icon": t["authorThumbnails"][-1]["url"],
            "channel_profile": t["descriptionHtml"],
            "author_banner": urllib.parse.quote(t["authorBanners"][0]["url"], safe="-_.~/:") if 'authorBanners' in t and len(t['authorBanners']) else '',
            "subscribers_count": t["subCount"],
            "tags": t["tags"]
        }
    ]

def getPlaylistData(listid, page):
    t = json.loads(requestAPI(f"/playlists/{urllib.parse.quote(listid)}?page={urllib.parse.quote(page)}", invidious_api.playlist))["videos"]
    return [{"title": i["title"], "id": i["videoId"], "authorId": i["authorId"], "author": i["author"], "type": "video"} for i in t]

def getCommentsData(videoid):
    t = json.loads(requestAPI(f"/comments/{urllib.parse.quote(videoid)}?hl=jp", invidious_api.comments))["comments"]
    return [{"author": i["author"], "authoricon": i["authorThumbnails"][-1]["url"], "authorid": i["authorId"], "body": i["contentHtml"].replace("\n", "<br>")} for i in t]

'''
使われていないし戻り値も設定されていないためコメントアウト
def get_replies(videoid, key):
    t = json.loads(requestAPI(f"/comments/{videoid}?hmac_key={key}&hl=jp&format=html", invidious_api.comments))["contentHtml"]
'''


def checkCookie(cookie):
    isTrue = True if cookie == "True" else False
    return isTrue

def getVerifyCode():
    try:
        result = subprocess.run(["./yukiverify"], encoding='utf-8', stdout=subprocess.PIPE)
        hashed_password = result.stdout.strip()
        return hashed_password
    except subprocess.CalledProcessError as e:
        print(f"getVerifyCode__Error: {e}")
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
app.mount("/js", StaticFiles(directory="./js"), name="static")
app.mount("/css", StaticFiles(directory="./css"), name="static")
app.mount("/croissantrecipe", StaticFiles(directory="./blog", html=True), name="static")
app.add_middleware(GZipMiddleware, minimum_size=1000)

from fastapi.templating import Jinja2Templates
template = Jinja2Templates(directory='templates').TemplateResponse

no_robot_meta_tag = '<meta name="robots" content="noindex,nofollow">'

@app.get("/", response_class=HTMLResponse)
def home(response: Response, request: Request, yuki: Union[str] = Cookie(None)):
    if checkCookie(yuki):
        response.set_cookie("yuki", "True", max_age=60 * 60 * 24 * 7)
        return template("home.html", {"request": request})
    print(checkCookie(yuki))
    return redirect("/croissantrecipe")


@app.get('/watch', response_class=HTMLResponse)
def video(v:str, response: Response, request: Request, yuki: Union[str] = Cookie(None), proxy: Union[str] = Cookie(None)):
    # v: video_id
    if not(checkCookie(yuki)):
        return redirect("/")
    response.set_cookie(key="yuki", value="True", max_age=7*24*60*60)
    video_data = getVideoData(v)
    '''
    return [
        {
            'video_urls': list(reversed([i["url"] for i in t["formatStreams"]]))[:2],
            'description_html': t["descriptionHtml"].replace("\n", "<br>"),
            'title': t["title"],
            'length_text': str(datetime.timedelta(seconds=t["lengthSeconds"]))
            'author_id': t["authorId"],
            'author': t["author"],
            'author_thumbnails_url': t["authorThumbnails"][-1]["url"],
            'view_count': t["viewCount"],
            'like_count': t["likeCount"],
            'subscribers_count': t["subCountText"]
        },
        [
            {
                "video_id": i["videoId"],
                "title": i["title"],
                "author_id": i["authorId"],
                "author": i["author"],
                "length_text": str(datetime.timedelta(seconds=i["lengthSeconds"])),
                "view_count_text": i["viewCountText"]
            } for i in recommended_videos
        ]
    ]
    '''
    response.set_cookie("yuki", "True", max_age=60 * 60 * 24 * 7)
    return template('video.html', {
        "request": request,
        "videoid": v,
        "videourls": video_data[0]['video_urls'],
        "description": video_data[0]['description_html'],
        "video_title": video_data[0]['title'],
        "author_id": video_data[0]['author_id'],
        "author_icon": video_data[0]['author_thumbnails_url'],
        "author": video_data[0]['author'],
        "length_text": video_data[0]['length_text'],
        "view_count": video_data[0]['view_count'],
        "like_count": video_data[0]['like_count'],
        "subscribers_count": video_data[0]['subscribers_count'],
        "recommended_videos": video_data[1],
        "proxy":proxy
    })

@app.get("/search", response_class=HTMLResponse)
def search(q:str, response: Response, request: Request, page:Union[int, None]=1, yuki: Union[str] = Cookie(None), proxy: Union[str] = Cookie(None)):
    if not(checkCookie(yuki)):
        return redirect("/")
    response.set_cookie("yuki", "True", max_age=60 * 60 * 24 * 7)
    return template("search.html", {"request": request, "results":getSearchData(q, page), "word":q, "next":f"/search?q={q}&page={page + 1}", "proxy":proxy})

@app.get("/hashtag/{tag}")
def search(tag:str, response: Response, request: Request, page:Union[int, None]=1, yuki: Union[str] = Cookie(None)):
    if not(checkCookie(yuki)):
        return redirect("/")
    return redirect(f"/search?q={tag}")

@app.get("/channel/{channelid}", response_class=HTMLResponse)
def channel(channelid:str, response: Response, request: Request, yuki: Union[str] = Cookie(None), proxy: Union[str] = Cookie(None)):
    if not(checkCookie(yuki)):
        return redirect("/")
    response.set_cookie("yuki", "True", max_age=60 * 60 * 24 * 7)
    t = getChannelData(channelid)
    return template("channel.html", {"request": request, "results": t[0], "channel_name": t[1]["channel_name"], "channel_icon": t[1]["channel_icon"], "channel_profile": t[1]["channel_profile"], "cover_img_url": t[1]["author_banner"], "subscribers_count": t[1]["subscribers_count"], "proxy": proxy})

@app.get("/playlist", response_class=HTMLResponse)
def playlist(list:str, response: Response, request: Request, page:Union[int, None]=1, yuki: Union[str] = Cookie(None), proxy: Union[str] = Cookie(None)):
    if not(checkCookie(yuki)):
        return redirect("/")
    response.set_cookie("yuki", "True", max_age=60 * 60 * 24 * 7)
    return template("search.html", {"request": request, "results": getPlaylistData(list, str(page)), "word": "", "next": f"/playlist?list={list}", "proxy": proxy})

@app.get("/comments")
def comments(request: Request, v:str):
    return template("comments.html", {"request": request, "comments": getCommentsData(v)})

@app.get("/thumbnail")
def thumbnail(v:str):
    return Response(content = requests.get(f"https://img.youtube.com/vi/{v}/0.jpg").content, media_type=r"image/jpeg")

@app.get("/suggest")
def suggest(keyword:str):
    return [i[0] for i in json.loads(requests.get("http://www.google.com/complete/search?client=youtube&hl=ja&ds=yt&q=" + urllib.parse.quote(keyword), headers=header).text[19:-1])[1]]


@cache(seconds=120)
def getSource(name):
    return requests.get(f'https://raw.githubusercontent.com/LunaKamituki/yuki-source/refs/heads/main/{name}.html', headers=header).text

@app.get("/bbs", response_class=HTMLResponse)
def bbs(request: Request, name: Union[str, None] = "", seed:Union[str, None]="", channel:Union[str, None]="main", verify:Union[str, None]="false", yuki: Union[str] = Cookie(None)):
    if not(checkCookie(yuki)):
        return redirect("/")
    res = HTMLResponse(no_robot_meta_tag + requests.get(f"{url}bbs?name={urllib.parse.quote(name)}&seed={urllib.parse.quote(seed)}&channel={urllib.parse.quote(channel)}&verify={urllib.parse.quote(verify)}", cookies={"yuki":"True"}).text.replace('AutoLink(xhr.responseText);', 'urlConvertToLink(xhr.responseText);') + getSource('bbs'))
    return res

@cache(seconds=5)
def getCachedBBSAPI(verify, channel):
    return requests.get(f"{url}bbs/api?t={urllib.parse.quote(str(int(time.time()*1000)))}&verify={urllib.parse.quote(verify)}&channel={urllib.parse.quote(channel)}", cookies={"yuki":"True"}).text

@app.get("/bbs/api", response_class=HTMLResponse)
def bbsAPI(request: Request, t: str, channel:Union[str, None]="main", verify: Union[str, None] = "false"):
    return getCachedBBSAPI(verify, channel)

@app.get("/bbs/result")
def write_bbs(request: Request, name: str = "", message: str = "", seed:Union[str, None] = "", channel:Union[str, None]="main", verify:Union[str, None]="false", yuki: Union[str] = Cookie(None)):
    if not(checkCookie(yuki)):
        return redirect("/")
    if 'Google-Apps-Script' in str(request.scope["headers"][1][1]):
        raise UnallowedBot("GASのBotは許可されていません")
    
    t = requests.get(f"{url}bbs/result?name={urllib.parse.quote(name)}&message={urllib.parse.quote(message)}&seed={urllib.parse.quote(seed)}&channel={urllib.parse.quote(channel)}&verify={urllib.parse.quote(verify)}&info={urllib.parse.quote(getInfo(request))}&serververify={getVerifyCode()}", cookies={"yuki":"True"}, allow_redirects=False)
    if t.status_code != 307:
        return HTMLResponse(no_robot_meta_tag + t.text.replace('AutoLink(xhr.responseText);', 'urlConvertToLink(xhr.responseText);') + getSource('bbs'))
        
    return redirect(f"/bbs?name={urllib.parse.quote(name)}&seed={urllib.parse.quote(seed)}&channel={urllib.parse.quote(channel)}&verify={urllib.parse.quote(verify)}")

@cache(seconds=120)
def getCachedBBSHow():
    return requests.get(f"{url}bbs/how").text

@app.get("/bbs/how", response_class=PlainTextResponse)
def view_commonds(request: Request, yuki: Union[str] = Cookie(None)):
    if not(checkCookie(yuki)):
        return redirect("/")
    return getCachedBBSHow()

@app.get("/info", response_class=HTMLResponse)
def viewlist(response: Response, request: Request, yuki: Union[str] = Cookie(None)):
    if not(checkCookie(yuki)):
        return redirect("/")
    response.set_cookie("yuki", "True", max_age=60 * 60 * 24 * 7)
    
    return template("info.html", {"request": request, "Youtube_API": invidious_api.video[0], "Channel_API": invidious_api.channel[0], "comments": invidious_api.comments[0]})

@app.get("/reset", response_class=PlainTextResponse)
def home():
    global url, invidious_api
    url = requests.get('https://raw.githubusercontent.com/mochidukiyukimi/yuki-youtube-instance/refs/heads/main/instance.txt', headers=header).text.rstrip()
    invidious_api = InvidiousAPI()
    return 'Success'

@app.get("/version", response_class=PlainTextResponse)
def displayVersion():
    return str({'version': version, 'new_instance_version': new_instance_version})

@app.get("/api", response_class=PlainTextResponse)
def displayAPI():
    return str(invidious_api.info())
    
@app.get("/api/update", response_class=PlainTextResponse)
def updateAPI():
    global invidious_api
    invidious_api = InvidiousAPI()
    return 'Success'

@app.get("/api/channel", response_class=PlainTextResponse)
def displaychannel():
    return str(invidious_api.channel)

@app.get("/api/comments", response_class=PlainTextResponse)
def displayComments():
    return str(invidious_api.comments)


@app.get("/api/video", response_class=PlainTextResponse)
def displayvideo():
    return str(invidious_api.video)

@app.get("/api/video/next", response_class=PlainTextResponse)
def updatevideoAPI():
    return str(updateList(invidious_api.video, invidious_api.video[0]))
    
@app.get("/api/video/check", response_class=PlainTextResponse)
def displayCheckVideo():
    return str(invidious_api.check_video)

@app.get("/api/video/check/toggle", response_class=PlainTextResponse)
def toggleVideoCheck():
    global invidious_api
    invidious_api.check_video = not invidious_api.check_video
    return f'{not invidious_api.check_video} to {invidious_api.check_video}'


@app.exception_handler(500)
def error500(request: Request, __):
    return template("error.html", {"request": request, "context": '500 Internal Server Error'}, status_code=500)

@app.exception_handler(APITimeoutError)
def apiWait(request: Request, exception: APITimeoutError):
    return template("apiTimeout.html", {"request": request}, status_code=504)

@app.exception_handler(UnallowedBot)
def returnToUnallowedBot(request: Request, exception: UnallowedBot):
    return template("error.html", {"request": request, "context": '403 Forbidden'}, status_code=403)
