# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""This script downloads media from a YouTube link or an M3U8 playlist file."""

import os
import subprocess
import sys
import traceback
import click
from pytube import YouTube
from pytube import exceptions

FILES = []

@click.command()
@click.option('--url', prompt="Media URL? (enclose in quotes)",
              help="Link to YouTube video or M3U8 file.")
@click.option('--path', default=lambda: os.path.join(os.environ['HOME'], "Downloads"),
              type=click.Path(exists=True), help='Download path.')
@click.option('--filename', default='output.mp4', help='Output filename of download.')
@click.option('--info', is_flag=True, help='Display info about media stream.')
@click.option('--only_audio', is_flag=True, help='Save the audio only from YouTube media stream.')
@click.option('--audio_format', help='Output format of audio only stream.')


def main(filename, path, url, info, only_audio, audio_format):
    """This script downloads media from a YouTube link or an M3U8 playlist file."""
    os.system('clear')
    if '.m3u8' in url:
        download_m3u8(filename, path, url)
    else:
        download_youtube(path, url, info, only_audio, audio_format)
    
    return

def logerror():
    """Logs last error to screen."""
    print "\n\n!! Error -\n"

    print traceback.format_exc()
    sys.exit(1)

def download_m3u8(filename, path, url):
    """Downloads M3U8 playlist."""
    try:
        outpath = os.path.join(path, filename)
        print "M3U playlist detected."
        print " + Downloading " + url + " to " + outpath
        cmd = "ffmpeg -i " + url + " -c copy -bsf:a aac_adtstoasc " + outpath + " -loglevel error"
        ret = subprocess.call(cmd, shell=True)

        if ret == 0:
            print "Done."
        
        return

    except:
        logerror()

def download_youtube(path, url, info, only_audio, audio_format):
    """Downloads YouTube link."""
    print "only_audio is " + str(only_audio)

    try:
        yt_video = YouTube(url, on_progress_callback=progress_function,
                           on_complete_callback=filetrack_function)
        title = yt_video.title

        if info:
            print "Stream information:\n"
            for stream in yt_video.streams.all():
                print stream
            print "\n"
            return

        print "Determining streams:"
        streams = stream_determinator(yt_video, only_audio)

        print "\nDownloading YouTube media '" + title + "' to " + path

        for media in streams:
            if len(streams) > 1:
                prefix = str(media.type + "-")
            else:
                prefix = str("")

            print " + Downloading " + media.type + " - " + media.default_filename + "\n"
            media.download(output_path=path, filename_prefix=prefix)
            print "\n"

        if len(streams) > 1:
            combine_function(path, title)

        if only_audio and audio_format:
            convert_function(path, title, audio_format)
        else:
            print "Done."
        
        return

    except (exceptions.RegexMatchError, exceptions.VideoUnavailable):
        logerror()

def stream_determinator(yt_video, only_audio):
    """Determines if a seperate 1080p mp4 video stream exists. \
    If it does, download it and its associated audio stream. \
    Else download highest resolution video stream."""
    try:
        streams = []

        if only_audio:
            audio = yt_video.streams.filter(only_audio=True, only_video=False,
                                            ).order_by('abr').desc().first()
            streams.append(audio)
        else:
            video = yt_video.streams.filter(only_audio=False, only_video=True,
                                        subtype='mp4').order_by('resolution').desc().first()

            if video is not None:
                print " + Found seperate video stream - adding"
                audio = yt_video.streams.filter(only_audio=True, only_video=False,
                                                subtype='mp4').order_by('abr').desc().first()
                if audio is not None:
                    print " + Found seperate audio stream - adding"
                    streams.append(audio)
            else:
                print " - Only single stream detected"
                video = yt_video.streams.filter(only_audio=False,
                                                subtype='mp4').order_by('resolution').desc().first()

            streams.append(video)

        return streams

    except exceptions.VideoUnavailable:
        logerror()

def progress_function(stream, chunk, file_handle, bytes_remaining):
    """Displays progress bar as YouTube link is downloaded."""
    filesize = stream.filesize
    bytes_received = filesize - bytes_remaining
    display_progress_bar(bytes_received, filesize)

def display_progress_bar(bytes_received, filesize, char='█', scale=0.55):
    """Displays progress bar as YouTube link is downloaded."""
    _, columns = get_terminal_size()
    max_width = int(columns * scale)

    filled = int(round(max_width * bytes_received / float(filesize)))
    remaining = max_width - filled
    perc_bar = char * filled + ' ' * remaining
    percent = round(100.0 * bytes_received / float(filesize), 1)
    text = ' [⇩]{bar}| {percent}%\r'.format(bar=perc_bar, percent=percent)
    sys.stdout.write(text)
    sys.stdout.flush()

def get_terminal_size():
    """Gets Terminal size."""
    rows, columns = os.popen('stty size', 'r').read().split()
    return int(rows), int(columns)

def filetrack_function(stream, file_handle):
    """Tracks which files have been downloaded. Used by combine function."""
    try:
        FILES.append(file_handle.name)
        return

    except:
        logerror()

def combine_function(path, title):
    """Combines seperate audio and video stream files."""
    try:
        title = title.replace(":", "-")
        for mediafile in FILES:
            if 'audio-' in mediafile:
                audio = mediafile
            else:
                video = mediafile

        outpath = os.path.join(path, title)
        outpath = outpath.replace("'", "")

        cmd = "ffmpeg -y -i '" + audio + "' -i '" + video + \
              "' -c copy '" + outpath + ".mp4' -loglevel error"
        print "Combining..."
        #print cmd
        ret = subprocess.call(cmd, shell=True)

        if ret == 0:
            print "Done."

        cleanup()
        return

    except:
        logerror()

def convert_function(path, title, audio_format):
    """Converts YouTube audio stream files to the desired format."""
    try:
        title = title.replace(":", "-")
        for mediafile in FILES:
            audio = mediafile

        outpath = os.path.join(path, title)
        outpath = outpath.replace("'", "")

        cmd = "ffmpeg -y -i '" + audio + "' -vn '" + outpath + "." + audio_format + "' -loglevel error"
        print "Converting " + title + " to " + audio_format + "..."
        #print cmd
        ret = subprocess.call(cmd, shell=True)

        if ret == 0:
            print "Done."

        cleanup()
        return

    except:
        logerror()

def cleanup():
    """Deletes source audio and video stream after combining."""
    try:
        for mediafile in FILES:
            os.remove(mediafile)
        return

    except:
        logerror()

if __name__ == '__main__':
    main()
