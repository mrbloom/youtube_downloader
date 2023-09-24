import tkinter as tk
from tkinter import simpledialog, messagebox
from pytube import YouTube
from moviepy.editor import concatenate_audioclips, AudioFileClip, VideoFileClip


def download_and_combine():
    url = url_entry.get()

    yt = YouTube(url)

    # Get the video stream with the highest resolution without audio codec
    video_stream = yt.streams.filter(only_video=True, file_extension='mp4').order_by("resolution").desc().first()

    # Get the best audio stream
    audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').first()

    if not video_stream or not audio_stream:
        messagebox.showerror("Error", "Suitable streams not found.")
        return

    status_label.config(text=f"Downloading video: {yt.title} in {video_stream.resolution}")
    video_filename = video_stream.download(filename="video_temp")

    status_label.config(text=f"Downloading audio for: {yt.title}")
    audio_filename = audio_stream.download(filename="audio_temp")

    status_label.config(text="Combining video and audio...")
    video = VideoFileClip(video_filename)
    audio = AudioFileClip(audio_filename)

    final_clip = video.set_audio(audio)
    final_clip.write_videofile(f"{yt.title}.mp4")

    status_label.config(text="Download and merge completed!")
    messagebox.showinfo("Success", "Download and merge completed!")


# Create the main window
root = tk.Tk()
root.title("YouTube Downloader")

# Add an Entry widget for the user to enter the URL
url_entry = tk.Entry(root, width=50)
url_entry.pack(pady=20)
url_entry.insert(0, "Enter the YouTube video URL")

# Add a button to start the download process
download_button = tk.Button(root, text="Download", command=download_and_combine)
download_button.pack(pady=20)

# Add a label to show the status
status_label = tk.Label(root, text="", bd=1, relief="solid", anchor="w")
status_label.pack(pady=20, fill=tk.X)

root.mainloop()
