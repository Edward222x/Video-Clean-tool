import os
import subprocess
import whisper
from nudenet import NudeClassifier
from datetime import timedelta
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

def choose_file():
    filepath = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video files", "*.mp4 *.mov *.mkv")])
    if filepath:
        video_path.set(filepath)

def run_scan():
    video_file = video_path.get()
    if not os.path.isfile(video_file):
        messagebox.showerror("Error", "Invalid video file path.")
        return

    FRAME_DIR = "frames"
    FRAME_RATE = 1
    BAD_WORDS = {"fuck", "shit", "bitch", "damn", "asshole"}

    ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg.exe")
    if not os.path.exists(ffmpeg_path):
        messagebox.showerror("Error", "ffmpeg.exe not found in the application folder.")
        return

    try:
        print("🔊 Transcribing with Whisper...")
        model = whisper.load_model("medium")
        result = model.transcribe(video_file, word_timestamps=True)

        profanity_timestamps = []
        for segment in result['segments']:
            for word in segment.get("words", []):
                if word['word'].strip().lower() in BAD_WORDS:
                    start = str(timedelta(seconds=int(word['start'])))
                    profanity_timestamps.append((word['word'], start))

        print("🖼️ Extracting frames with local ffmpeg.exe...")
        if os.path.exists(FRAME_DIR):
            shutil.rmtree(FRAME_DIR)
        os.makedirs(FRAME_DIR)

        subprocess.run([
            ffmpeg_path, "-i", video_file,
            "-vf", f"fps={FRAME_RATE}",
            os.path.join(FRAME_DIR, "frame_%05d.jpg")
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print("🧠 Scanning frames for nudity with NudeNet...")
        classifier = NudeClassifier()
        nsfw_frames = []

        results = classifier.classify(FRAME_DIR)
        for frame_file, result in results.items():
            if result["unsafe"] > 0.5:
                frame_name = os.path.basename(frame_file)
                frame_num = int(frame_name.split("_")[1].split(".")[0])
                timestamp = str(timedelta(seconds=frame_num))
                nsfw_frames.append((frame_name, timestamp, result["unsafe"]))

        with open("scan_report.txt", "w") as f:
            f.write("⚠️ Profanity Detected:\n")
            for word, timestamp in profanity_timestamps:
                f.write(f" - {timestamp}: {word}\n")

            f.write("\n🚫 Nudity Detected in Frames:\n")
            for frame, timestamp, score in nsfw_frames:
                f.write(f" - {timestamp}: {frame} (NSFW score: {score:.2f})\n")

        messagebox.showinfo("Scan Complete", "Scan finished! Results saved to scan_report.txt.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# GUI setup
root = tk.Tk()
root.title("Video Clean Scan Tool")
root.geometry("500x200")

video_path = tk.StringVar()

tk.Label(root, text="Select your video file:").pack(pady=10)
tk.Entry(root, textvariable=video_path, width=60).pack()
tk.Button(root, text="Browse", command=choose_file).pack(pady=5)
tk.Button(root, text="Run Scan", command=run_scan, bg="green", fg="white").pack(pady=10)

root.mainloop()