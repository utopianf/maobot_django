import os
import re
import subprocess
from io import BytesIO
import urllib.request
from urllib.error import HTTPError
from urllib.parse import urlencode, quote
import uuid
from imghdr import what

import requests
from bs4 import BeautifulSoup
import PIL.Image

from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.temp import NamedTemporaryFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.signals import post_save
from django.dispatch import receiver

from ircimages.models import Image
from maobot.settings import SECRET_KEYS
from .models import Log


def image_from_response(response, image):
    if response.status_code == requests.codes.ok:
        img_temp = NamedTemporaryFile()
        img_temp.write(response.content)
        ext = what(img_temp.name)
        if ext is None:
            return None

        img_temp.flush()
        filename = '%s.%s' % (str(uuid.uuid4()).replace('-', ''), ext)
        # image file
        image.image.save(filename, File(img_temp))
        # thumbnail
        size = 150
        img = PIL.Image.open(img_temp)
        w, h = img.size
        l, t, r, b = 0, 0, size, size
        new_w, new_h = size, size

        if w >= h:
            new_w = size * w // h
            l = (new_w - size) // 2
            r = new_w - l
        else:
            new_h = size * h // w
            t = (new_h - size) // 2
            b = new_h - t

        thumb = img.resize((new_w, new_h), PIL.Image.ANTIALIAS)
        thumb = thumb.crop((l, t, r, b))
        thumb_io = BytesIO()
        thumb.save(thumb_io, format=ext)

        thumb_file = InMemoryUploadedFile(ContentFile(thumb_io.getvalue()), None, 't_' + filename, 'image/' + ext,
                                          ContentFile(thumb_io.getvalue()).tell, None)
        image.thumb.save('t_' + filename, thumb_file)
        return image
    return None


@receiver(post_save, sender=Log)
def check_log(instance, **kwargs):
    log = instance
    print(log)
    if log.command == 'PRIVMSG':
        url_pat = re.compile(r"https?://[a-zA-Z0-9\-./?@&=:~_#]+")
        url_list = re.findall(url_pat, log.message)
        for url in url_list:
            r = requests.get(url)
            if r.status_code != 403:
                content_type_encoding = r.encoding if r.encoding != 'ISO-8859-1' else None
                soup = BeautifulSoup(r.content, 'html.parser', from_encoding=content_type_encoding)
                try:
                    title = soup.title.string.replace("\n", " ")
                    Log(command='NOTICE', channel=log.channel,
                        nick='maobot', message=title, is_irc=False).save()

                except (AttributeError, TypeError, HTTPError):
                    pass

            # image dl
            nicoseiga_pat = re.compile(
                'http://seiga.nicovideo.jp/seiga/[a-zA-Z]+([0-9]+)')
            pixiv_pat = re.compile(
                'https://www.pixiv.net/member_illust.php/?\?([a-zA-Z0-9\-./?@&=:~_#]+)')
            pixiv_pat_2 = re.compile(
                    'https://i.pximg.net/img-((master)|(original))/img/([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+)_p([0-9]+)(_master1200)?.((jpg)|(png))')
            twitter_pat = re.compile(
                'https://twitter.com/[a-zA-Z0-9_]+/status/\d+')
            image_format = ["jpg", "jpeg", "gif", "png"]

            if twitter_pat.match(url):
                try:
                    images = soup.find("div", {"class": "permalink-tweet-container"}).find("div", {"class": "AdaptiveMedia-container"}).findAll("div", {"class": "AdaptiveMedia-photoContainer"})
                except AttributeError:
                    images = soup.findAll("div", {"class": "media"})
                for image in images:
                    try:
                        image_url = image.find('img')['src']
                        img = image_from_response(requests.Session().get(image_url),
                                                Image(original_url=url, related_log=log, caption=title))
                        img.save()
                        Log.objects.filter(id=log.id).update(attached_image=img.thumb)
                    except Exception as e:
                        print(e)
            elif nicoseiga_pat.match(url):
                seiga_login = 'https://secure.nicovideo.jp/secure/login'
                seiga_id = nicoseiga_pat.search(url).group(1)
                seiga_source = 'http://seiga.nicovideo.jp/image/source/%s' % seiga_id
                login_post = {'mail_tel': SECRET_KEYS['nicouser'],
                              'password': SECRET_KEYS['nicopass']}

                session = requests.Session()
                session.post(seiga_login, data=login_post)
                soup = BeautifulSoup(session.get(seiga_source).text, 'lxml')
                image_url = 'http://lohas.nicoseiga.jp%s' % soup.find(
                    'div', {'class': 'illust_view_big'})['data-src']
                img = image_from_response(requests.Session().get(image_url),
                        Image(original_url=url, related_log=log, caption=soup.title.string[:-16]))
                img.save()
                Log.objects.filter(id=log.id).update(attached_image=img.thumb)
            elif pixiv_pat.match(url):
                from pixivpy3 import AppPixivAPI
                from urllib.parse import parse_qs
                api = AppPixivAPI()
                api.login(SECRET_KEYS['pixiuser'], SECRET_KEYS['pixipass'])
                pixiv_query = pixiv_pat.search(url).group(1)
                pixiv_dict = parse_qs(pixiv_query)
                pixiv_id = pixiv_dict['illust_id']
                pixiv_illust = api.illust_detail(pixiv_id, req_auth=True).illust
                if 'meta_pages' in pixiv_illust and len(pixiv_illust.meta_pages) != 0:
                    image_urls = []
                    if 'page' in pixiv_dict:
                        image_urls.append(pixiv_illust.meta_pages[int(pixiv_dict['page'][0])].image_urls.original)
                    else:
                        for i in pixiv_illust.meta_pages:
                            image_urls.append(i.image_urls.original)
                else:
                    image_urls = [pixiv_illust.meta_single_page.original_image_url]
                for image_url in image_urls:
                    response = api.requests_call('GET', image_url,
                                                 headers={'Referer': 'https://app-api.pixiv.net/'},
                                                 stream=True)
                    img = image_from_response(response,
                                              Image(original_url=url, related_log=log, caption=pixiv_illust.title))
                    img.save()
                    Log.objects.filter(id=log.id).update(attached_image=img.thumb)
            elif pixiv_pat_2.match(url):
                from pixivpy3 import AppPixivAPI
                api = AppPixivAPI()
                api.login(SECRET_KEYS['pixiuser'], SECRET_KEYS['pixipass'])
                pixiv_id = pixiv_pat_2.search(url).group(10)
                pixiv_illust = api.illust_detail(pixiv_id, req_auth=True).illust
                response = api.requests_call('GET', url,
                                             headers={'Referer': 'https://app-api.pixiv.net/'},
                                             stream=True)
                img = image_from_response(response,
                                          Image(original_url=url, related_log=log, caption=pixiv_illust.title))
                img.save()
                Log.objects.filter(id=log.id).update(attached_image=img.thumb)

            elif url.split(".")[-1] in image_format:
                img = image_from_response(requests.Session().get(url),
                                          Image(original_url=url, related_log=log))
                img.save()
                Log.objects.filter(id=log.id).update(attached_image=img.thumb)
