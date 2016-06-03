#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from urllib.parse import urlparse, parse_qs
import os
import json
from collections import OrderedDict


def get_videos(path):
    for dir_path, dir_name, filenames in os.walk(path):
        for filename in filenames:
            if filename != 'category.json':
                filepath = "{}/{}".format(dir_path, filename)
                with open(filepath) as f:
                    video = json.load(f)
                    yield video, filepath


def order_video_json(video):
    vid_order = ['url', 'type', 'length']

    vid_videos = []
    for vid in video['videos']:
        for key in vid_order:
            vid_videos.append((key, vid[key]))
    video['videos'] = OrderedDict(vid_videos)

    order = ['id', 'category', 'slug', 'title', 'summary', 'description',
             'quality_notes', 'language', 'copyright_text', 'thumbnail_url',
             'duration', 'videos', 'source_url', 'tags', 'speakers',
             'recorded']
    ordered_dict = []

    for key in order:
        ordered_dict.append((key, video[key]))

    return OrderedDict(ordered_dict)


def write_video(video, filepath):
    with open(filepath, 'w') as f:
        f.write(json.dumps(order_video_json(video),
                           indent=2,
                           sort_keys=False,
                           separators=(',', ': '),
                           ))


def get_last_id(videos):
    ids = []
    for video, _ in get_videos(path):
        if 'id' in video and video['id']:
            ids.append(video['id'])

    next_id = sorted([id for id in ids if id], reverse=True)[0] + 1
    return next_id


def get_source_url(video):
    if video['source_url']:
        return video['source_url']


def get_non_souce_urls(video):
    urls = []
    if video['videos']:
        urls += [item['url'] for item in video['videos']]
    else:
        with open('./no_source.txt', 'a') as f:
            f.write(video['title'] + '\n')
    return urls


def fix_url(old_url):
    if old_url:
        url = urlparse(old_url)
        if 'youtu.be' in url.netloc:  # or 'youtube.com' in url.netloc:
            base_url = 'https://www.youtube.com'
            if 'youtu.be' in url.netloc:
                video_id = url.path.strip('/')
            else:
                video_id = parse_qs(url.query)['v'][0]
            new_url = "{}/watch?v={}".format(base_url, video_id)
        else:
            new_url = old_url
        return new_url


if __name__ == "__main__":
    if os.path.exists('./no_source.txt'):
        os.remove('./no_source.txt')

    path = './data/'

    videos = [video for video in get_videos(path)]
    next_id = get_last_id(videos)

    for video, filepath in get_videos(path):
        changed = False
        if not video.get('id') or not video['id']:
            video['id'] = next_id
            changed = True

        source_url = get_source_url(video)
        non_source_urls = get_non_souce_urls(video)

        new_source_url = fix_url(source_url)
        if new_source_url != source_url:
            video['source_url'] = new_source_url
            changed = True

        new_non_source_urls = [fix_url(url) for url in non_source_urls]

        for vid, new_url, old_url in zip(
                video['videos'], new_non_source_urls, non_source_urls):
            if new_url != old_url:
                vid['url'] = new_url
                changed = True

        if changed:
            write_video(video, filepath)
