import os
import shutil
import tkinter as tk
from tkinter import messagebox, ttk
from pytube import YouTube
from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.config import change_settings

def is_ffmpeg_installed():
    """ Check if ffmpeg is installed on the system """
    return shutil.which("ffmpeg") is not None

def set_local_ffmpeg_binary():
    """ Set the path to the local ffmpeg binary """
    current_folder = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_binary = os.path.join(current_folder, "ffmpeg.exe")
    change_settings({"FFMPEG_BINARY": ffmpeg_binary})

# Check if ffmpeg is installed, otherwise use the local ffmpeg
if not is_ffmpeg_installed():
    set_local_ffmpeg_binary()

def paste_from_clipboard(event):
    """ Handle paste operation from the clipboard """
    try:
        text = event.widget.clipboard_get()
        event.widget.insert(tk.INSERT, text)
    except tk.TclError:
        pass  # Do nothing if clipboard is empty or contains non-text data



def fetch_resolutions(url):
    yt = YouTube(url)
    streams = yt.streams.filter(file_extension='mp4')
    resolutions = sorted({stream.resolution for stream in streams if stream.resolution},
                         key=lambda x: -int(x.rstrip('p')))
    return resolutions


def download_video(url, resolution):
    yt = YouTube(url)
    video_stream = yt.streams.filter(only_video=True, resolution=resolution, file_extension='mp4').first()
    audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').first()

    if not video_stream or not audio_stream:
        raise RuntimeError("Suitable streams not found.")

    video_filename = video_stream.download(filename="video_temp")
    audio_filename = audio_stream.download(filename="audio_temp")

    return video_filename, audio_filename, yt.title


def combine_video_audio(video_filename, audio_filename, title):
    with VideoFileClip(video_filename) as video, AudioFileClip(audio_filename) as audio:
        final_clip = video.set_audio(audio)
        final_clip.write_videofile(f"{title}.mp4")


def cleanup_files(video_filename, audio_filename):
    os.remove(video_filename)
    os.remove(audio_filename)


def download_and_combine(url, resolution):
    try:
        video_filename, audio_filename, title = download_video(url, resolution)
        combine_video_audio(video_filename, audio_filename, title)
        cleanup_files(video_filename, audio_filename)
        messagebox.showinfo("Success", "Download and merge completed!")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def on_fetch_resolutions_button_clicked(url_entry, resolution_combobox):
    try:
        url = url_entry.get()
        resolutions = fetch_resolutions(url)
        resolution_combobox["values"] = resolutions
        if resolutions:
            resolution_combobox.current(0)
    except Exception as e:
        messagebox.showerror("Error", str(e))


# GUI Setup
root = tk.Tk()
root.title("YouTube Downloader")

url_entry = tk.Entry(root, width=50)
url_entry.pack(pady=20)
url_entry.bind("<Control-v>", paste_from_clipboard)  # Bind Ctrl+V to paste function

fetch_resolutions_button = tk.Button(root, text="Fetch Resolutions",
                                     command=lambda: on_fetch_resolutions_button_clicked(url_entry, resolution_combobox))
fetch_resolutions_button.pack(pady=5)

resolution_combobox = ttk.Combobox(root, state="readonly")
resolution_combobox.pack(pady=10)

download_button = tk.Button(root, text="Download",
                            command=lambda: download_and_combine(url_entry.get(), resolution_combobox.get()))
download_button.pack(pady=10)

root.mainloop()