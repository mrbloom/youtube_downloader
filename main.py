import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from pytube import YouTube, Stream
from moviepy.editor import VideoFileClip, AudioFileClip

def progress(stream: Stream, chunk: bytes, bytes_remaining: int):
    current = stream.filesize - bytes_remaining
    percentage = (current / stream.filesize) * 100
    progress_bar["value"] = percentage
    root.update_idletasks()

    # Command line progress
    cmd_line.insert(tk.END, f"\rProgress: {percentage:.2f}%")
    cmd_line.see(tk.END)

def fetch_resolutions(event=None):
    fetching_label.config(text="Fetching resolutions...")
    root.update_idletasks()
    url = url_entry.get()
    try:
        resolutions = get_resolutions(url)
        resolution_combobox["values"] = resolutions
        if resolutions:
            resolution_combobox.current(0)  # Automatically select the highest resolution
    except Exception as e:
        messagebox.showerror("Error", str(e))
    fetching_label.config(text="Resolutions fetched!")
    cmd_line.insert(tk.END, "\nResolutions fetched.\n")
    cmd_line.see(tk.END)

def get_resolutions(url):
    yt = YouTube(url)

    # Fetch both video-only and combined streams, then extract unique resolutions
    streams = yt.streams.filter(file_extension='mp4')
    resolutions = sorted({stream.resolution for stream in streams if stream.resolution}, key=lambda x: -int(x.rstrip('p')))

    return resolutions

def download_and_combine():
    url = url_entry.get()
    selected_resolution = resolution_combobox.get()

    yt = YouTube(url)
    yt.register_on_progress_callback(progress)

    video_stream = yt.streams.filter(only_video=True, resolution=selected_resolution, file_extension='mp4').first()
    audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').first()

    if not video_stream or not audio_stream:
        messagebox.showerror("Error", "Suitable streams not found.")
        return

    # Downloading and combining code
    video_filename = video_stream.download(filename="video_temp")
    audio_filename = audio_stream.download(filename="audio_temp")

    video = VideoFileClip(video_filename)
    audio = AudioFileClip(audio_filename)

    final_clip = video.set_audio(audio)
    final_clip.write_videofile(f"{yt.title}.mp4")

    cmd_line.insert(tk.END, "\nDownload and merge completed!")
    cmd_line.see(tk.END)

root = tk.Tk()
root.title("YouTube Downloader")

url_entry = tk.Entry(root, width=50)
url_entry.pack(pady=20)
url_entry.insert(0, "Enter the YouTube video URL")
url_entry.bind("<Button-1>", lambda e: url_entry.delete(0, tk.END))
url_entry.bind("<Return>", fetch_resolutions)  # When Enter is pressed after typing the URL

instruction_label = tk.Label(root, text="Press 'Enter' after entering the URL to fetch resolutions.")
instruction_label.pack(pady=5)

resolution_combobox = ttk.Combobox(root, state="readonly")
resolution_combobox.pack(pady=10)

fetching_label = tk.Label(root, text="")
fetching_label.pack(pady=5)

download_button = tk.Button(root, text="Download", command=download_and_combine)
download_button.pack(pady=10)

progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=400)
progress_bar.pack(pady=20)

# Command line display
cmd_line = scrolledtext.ScrolledText(root, undo=True, wrap=tk.WORD, width=50, height=5)
cmd_line.pack(pady=20, fill=tk.BOTH, expand=True)
cmd_line.config(font='TkFixedFont')
cmd_line.insert(tk.END, "Command line output:\n")

root.mainloop()
