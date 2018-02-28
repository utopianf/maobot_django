import os
import re
import subprocess
from io import BytesIO
import urllib.request
import uuid
from imghdr import what

import requests
from bs4 import BeautifulSoup
import PIL

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
    if log.nick != 'maobot':
        url_pat = re.compile(r"https?://[a-zA-Z0-9\-./?@&=:~_#]+")
        url_list = re.findall(url_pat, log.message)
        for url in url_list:
            response = urllib.request.urlopen(url)
            soup = BeautifulSoup(response, 'lxml')
            try:
                title = soup.title.string
                Log(command='NOTICE', channel=log.channel,
                    nick='maobot', message=title).save()

                # send to irc channel
                sendstr = 'NOTICE %s :%s' % (log.channel, title)
                cmd = "echo '%s' > /tmp/run/irc3/:raw" % sendstr
                if os.path.isdir('/tmp/run/irc3'):
                    subprocess.call(cmd, shell=True)
            except (AttributeError, TypeError):
                pass

            # image dl
            nicoseiga_pat = re.compile(
                'http://seiga.nicovideo.jp/seiga/[a-zA-Z]+([0-9]+)')
            pixiv_pat = re.compile(
                'https://www.pixiv.net/member_illust.php/?\?([a-zA-Z0-9\-./?@&=:~_#]+)')
            twitter_pat = re.compile(
                'https://twitter.com/[a-zA-Z0-9_]+/status/\d+')

            if twitter_pat.match(url):
                images = soup.findAll('div', {'class': 'AdaptiveMedia-photoContainer'})
                for image in images:
                    image_url = image.find('img')['src']
                    img = image_from_response(requests.Session().get(image_url),
                                              Image(original_url=url, related_log=log))
                    img.save()
                    Log.objects.filter(id=log.id).update(attached_image=img.thumb)
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
                                          Image(original_url=url, related_log=log))
                img.save()
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
                    for i in pixiv_illust.meta_pages:
                        image_urls.append(i.image_urls.large)
                else:
                    image_urls = [pixiv_illust.image_urls.large]
                for image_url in image_urls:
                    response = api.requests_call('GET', image_url,
                                                 headers={'Referer': 'https://app-api.pixiv.net/'},
                                                 stream=True)
                    img = image_from_response(response,
                                              Image(original_url=url, related_log=log))
                    img.save()
