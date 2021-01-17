#!usr/env/bin python

import os
import sys

import youtube_dl
import ffmpeg

# TODO: command-line argument support
# TODO: - vod urls as a list of arguments
# TODO: - prefer 1080p option (720p default)
# TODO: - delete sped up vods and only keep concat version
# TODO: - option to overwrite output folder
# TODO: - option for how much to speed up video
# TODO: - option to keep audio in timelapse?
# TODO: once I add threading, check that all vod urls in input are unique to avoid conflicts
# TODO: handle vod list input through input() after running
# TODO: upload to pypi when done :)


YOUTUBE_DL_DEFAULT_OUTTMPL = '%(title)s-%(id)s.%(ext)s'

vods_list_file_path = 'vods.txt'
out_folder = 'downloads'
prefer_1080p = False
speed = 1000
# TODO: make sure you change this default!
clear_out_folder = True
output_timelapse_filename = 'timelapse.mp4'


def out_folder_empty(overwrite=clear_out_folder):
    try:
        out_folder_contents = os.listdir(out_folder)
    except FileNotFoundError:
        return True
    else:
        if overwrite:
            print(f"Clearing downloads folder '{out_folder}'..")
            for file in out_folder_contents:
                os.remove(os.path.join(out_folder, file))
            return True
        else:
            return not out_folder_contents


def vods_list_from_file(path=vods_list_file_path):
    try:
        with open(path, 'r') as vods_list_file:
            vods_list = vods_list_file.read().splitlines()
    except FileNotFoundError:
        print(f"List of VODs to download '{path}' not found.")
        sys.exit()
    else:
        return vods_list


def download(vods_list):
    ydl_args = {
        'outtmpl': f'/{out_folder}/{YOUTUBE_DL_DEFAULT_OUTTMPL}',
        'progress_hooks': [speed_up],
    }
    if not prefer_1080p:
        ydl_args['format'] = 'best[height<=720]'

    try:
        with youtube_dl.YoutubeDL(ydl_args) as ydl:
            ydl.download(vods_list)
    except youtube_dl.utils.DownloadError:
        # TODO: get invalid URL from error details and print it
        print('Invalid video URL, skipping.')


def speed_up(video_download):
    if not video_download['status'] == 'finished':
        return
    filename, file_extension = os.path.splitext(video_download['filename'])
    filename_no_extension = video_download['filename'][:-len(file_extension)]

    stream = ffmpeg.input(video_download['filename'])
    stream = ffmpeg.setpts(stream, f'(1/{speed})*PTS')
    stream = ffmpeg.output(stream, f"{filename_no_extension}-{speed}x{file_extension}")
    ffmpeg.run(stream)

    os.remove(video_download['filename'])


def combine_videos_in(folder=out_folder):
    videos = os.listdir(folder)

    streams = []
    for video in videos:
        streams.append(ffmpeg.input(os.path.join(folder, video)))
    stream = ffmpeg.output(*streams, os.path.join(folder, output_timelapse_filename), c='copy')
    ffmpeg.run(stream)

    for video in videos:
        os.remove(os.path.join(folder, video))


def main():
    if not out_folder_empty():
        print(f'The output folder {out_folder} contains files, please clear it.')
        sys.exit()

    vods_list = vods_list_from_file()
    download(vods_list)
    combine_videos_in(out_folder)

    print('Done.')


if __name__ == '__main__':
    main()
