import datetime
import os
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
from pytube import YouTube
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
        return "break"
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

    # Get the current date and time
    now = datetime.datetime.now()
    # Format the date and time as YYYYMMDDhhmmss
    formatted_date = now.strftime("%Y%m%d%H%M%S")

    video_filename = video_stream.download(filename=f"video_temp_{formatted_date}")
    audio_filename = audio_stream.download(filename=f"audio_temp_{formatted_date}")

    return video_filename, audio_filename, yt.title


def combine_video_audio(video_filename, audio_filename, title):
    output_filename = f"{title}.mp4"
    # Command to combine video and audio with FFmpeg
    command = [
        'ffmpeg',
        '-i', video_filename,
        '-i', audio_filename,
        '-c:v', 'copy',  # Copy the video stream
        '-c:a', 'copy',  # Convert audio to AAC
        '-strict', 'experimental',
        output_filename
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during combining video and audio: {e}")
        raise
    # with VideoFileClip(video_filename) as video, AudioFileClip(audio_filename) as audio:
    #     final_clip = video.set_audio(audio)
    #     final_clip.write_videofile(f"{title}.mp4")


def cleanup_files(video_filename, audio_filename):
    os.remove(video_filename)
    os.remove(audio_filename)

def sanitize_filename(filename):
    """
    Sanitize a string to be used as a Windows filename.

    :param filename: The original filename string.
    :return: A sanitized filename string.
    """
    # Windows filename forbidden characters: \/:*?"<>|
    forbidden_chars = '<>:"/\\|?*'

    # Replace each forbidden character with an underscore
    for char in forbidden_chars:
        filename = filename.replace(char, '_')

    return filename


def download_and_combine(url, resolution, keep_audio=False):
    try:
        video_filename, audio_filename, title = download_video(url, resolution)
        title = sanitize_filename(title)
        # if keep_audio:
        #     sanitized_video_filename = f"{title}_audioless.mp4"
        #     shutil.copy(video_filename, sanitized_video_filename)

        combine_video_audio(video_filename, audio_filename, title)

        # Download subtitles
        yt = YouTube(url)  # You might already have this object; if so, no need to create it again
        download_subtitles(yt, title)

        # Adjust cleanup based on keep_audio
        os.remove(video_filename)  # Always remove video temp file
        if keep_audio:
            sanitized_audio_filename = f"{title}.mp3"
            os.rename(audio_filename, sanitized_audio_filename)
        else:
            os.remove(audio_filename)

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

def download_subtitles(yt, title):
    """
    Download subtitles for a video if available and save them as a .srt file.
    """
    # Check if there are captions available
    captions = yt.captions.get_by_language_code('en')
    if captions:
        # Download and save the subtitles as a .srt file
        subtitles_filename = f"{title}.srt"
        with open(subtitles_filename, "w", encoding="utf-8") as f:
            f.write(captions.generate_srt_captions())
        print(f"Subtitles saved: {subtitles_filename}")
    else:
        print("No English subtitles available.")


# GUI Setup
root = tk.Tk()
root.title("YouTube Downloader")

# Create a label widget with descriptive text
label = tk.Label(root, text="Insert YouTube URL")
label.pack(pady=(10, 0))  # Add some padding above the label

url_entry = tk.Entry(root, width=50)
url_entry.pack(pady=20)
url_entry.bind("<Control-v>", paste_from_clipboard)  # Bind Ctrl+V to paste function


fetch_resolutions_button = tk.Button(root, text="Fetch Resolutions",
                                     command=lambda: on_fetch_resolutions_button_clicked(url_entry, resolution_combobox))
fetch_resolutions_button.pack(pady=5)

resolution_combobox = ttk.Combobox(root, state="readonly")
resolution_combobox.pack(pady=10)

# Create a variable to track the checkbox state
keep_audio_var = tk.IntVar(value=1)  # Default is not to keep

# Add a checkbox to the GUI
keep_audio_checkbox = tk.Checkbutton(root, text="Keep audio file separately", variable=keep_audio_var)
keep_audio_checkbox.pack()


download_button = tk.Button(root, text="Download",
                            command=lambda: download_and_combine(url_entry.get(), resolution_combobox.get(),
                            keep_audio_var.get()))

download_button.pack(pady=10)



root.mainloop()