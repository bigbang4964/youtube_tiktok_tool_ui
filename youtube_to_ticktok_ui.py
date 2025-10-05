# youtube_to_tiktok_ui.py
import os
import tempfile
import threading
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
import requests
from PIL import Image, ImageTk
import yt_dlp
from moviepy import (AudioFileClip, CompositeAudioClip, CompositeVideoClip,
                     ImageClip, TextClip, VideoFileClip, concatenate_videoclips)
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# ----------------- Utility -----------------
def search_youtube(query, max_results=10):
    ydl_opts = {'quiet': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_query = f"ytsearch{max_results}:{query}"
        info = ydl.extract_info(search_query, download=False)
        results = []
        for entry in info['entries']:
            duration = entry.get('duration') or 0
            if 60 <= duration <= 900:  # 1–15 phút
                results.append({
                    'title': entry.get('title'),
                    'id': entry.get('id'),
                    'url': entry.get('webpage_url'),
                    'duration': duration,
                    'view_count': entry.get('view_count', 0),
                    'thumbnail': entry.get('thumbnail'),
                })
        results.sort(key=lambda x: x['view_count'] or 0, reverse=True)
        return results

def download_video(url, out_path):
    ydl_opts = {
        'outtmpl': out_path,
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
    return info

def edit_video(input_path, output_path, caption_text=None, font='Arial', fontsize=40, fontcolor='white',
               watermark_path=None, watermark_pos=('right','bottom'),
               music_path=None, intro_path=None, outro_path=None):
    clips = []
    if intro_path:
        clips.append(VideoFileClip(intro_path))

    main_clip = VideoFileClip(input_path)
    if watermark_path:
        logo = (ImageClip(watermark_path)
                .set_duration(main_clip.duration)
                .resize(width=100)
                .margin(right=8, bottom=8, opacity=0)
                .set_pos(watermark_pos))
        main = CompositeVideoClip([main_clip, logo])
    else:
        main = main_clip

    if caption_text:
        txt = (TextClip(caption_text, fontsize=fontsize, font=font, color=fontcolor, method='caption', size=(main.w*0.9, None))
               .set_duration(main.duration)
               .set_pos(('center', main.h - fontsize*1.5)))
        main = CompositeVideoClip([main, txt])

    clips.append(main)

    if outro_path:
        clips.append(VideoFileClip(outro_path))

    final = concatenate_videoclips(clips, method="compose")

    if music_path:
        audioclip = AudioFileClip(music_path).fx(lambda a: a.volumex(0.6))
        audio = audioclip.set_duration(final.duration)
        orig = final.audio if final.audio else None
        if orig:
            final = final.set_audio(CompositeAudioClip([orig.volumex(1.0), audio.volumex(0.6)]))
        else:
            final = final.set_audio(audio)

    final.write_videofile(output_path, codec='libx264', audio_codec='aac')

def crop_16_9_to_9_16(input_path, output_path, face_center=True):
    clip = VideoFileClip(input_path)
    w, h = clip.size
    target_w, target_h = int(h*9/16), h
    x_center = w//2

    if face_center:
        frame = clip.get_frame(0)
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        if len(faces) > 0:
            x, y, fw, fh = faces[0]
            x_center = x + fw//2

    x1 = max(0, x_center - target_w//2)
    x2 = min(w, x1 + target_w)
    y1, y2 = 0, h
    cropped = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)
    cropped.write_videofile(output_path, codec='libx264', audio_codec='aac')

def upload_to_tiktok(video_path, caption=""):
    print("Uploading to TikTok:", video_path)
    print("Caption:", caption)
    return "1234567890"

def fetch_thumbnail(url):
    try:
        resp = requests.get(url, stream=True, timeout=5)
        img = Image.open(resp.raw).convert("RGB")
        img = img.resize((200, 120), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except:
        return None

# ----------------- GUI -----------------
class App:
    def __init__(self, root):
        self.root = root
        root.title("YouTube → TikTok Tool")
        root.geometry("1100x750")

        self.query_var = tk.StringVar()
        self.results = []
        self.thumbnail_img = None

        # Header
        header = tb.Label(root, text="YouTube → TikTok Video Tool", font=("Helvetica", 20, "bold"), bootstyle="inverse-primary", padding=10)
        header.pack(fill='x', pady=5)

        main_frame = tb.Frame(root, padding=10)
        main_frame.pack(fill='both', expand=True)

        # --- Search card ---
        search_frame = tb.Labelframe(main_frame, text="1. Tìm video trên YouTube", padding=10, bootstyle="info")
        search_frame.pack(fill='x', pady=5)

        tb.Label(search_frame, text="Từ khóa:").grid(row=0,column=0,sticky='w')
        tb.Entry(search_frame,textvariable=self.query_var,width=60).grid(row=0,column=1,sticky='w')
        tb.Button(search_frame,text="🔍 Tìm",command=self.on_search, bootstyle="success").grid(row=0,column=2,padx=5)

        # Video Listbox với scrollbar
        self.list_frame = tb.Frame(search_frame)
        self.list_frame.grid(row=1, column=0, columnspan=3, sticky='w')
        self.listbox = tk.Listbox(self.list_frame, width=80, height=8, selectmode=tk.SINGLE)
        self.listbox.pack(side='left', fill='y')
        self.scrollbar = tb.Scrollbar(self.list_frame, orient='vertical', command=self.listbox.yview)
        self.scrollbar.pack(side='left', fill='y')
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.listbox.bind('<<ListboxSelect>>', self.update_thumbnail)

        # Thumbnail preview
        self.thumbnail_label = tb.Label(search_frame, bootstyle="secondary")
        self.thumbnail_label.grid(row=0,column=3,rowspan=2, padx=10, pady=5)

        tb.Button(search_frame, text="▶️ Preview", command=self.preview, bootstyle="primary-outline").grid(row=2,column=1, pady=5, sticky='w')

        # --- Caption card ---
        caption_frame = tb.Labelframe(main_frame, text="2. Caption / Cài đặt nâng cao", padding=10, bootstyle="warning")
        caption_frame.pack(fill='x', pady=5)
        tb.Label(caption_frame, text="Caption:").grid(row=0,column=0,sticky='nw')
        self.caption_text = tb.Text(caption_frame,width=60,height=4)
        self.caption_text.grid(row=0,column=1,columnspan=2,sticky='w', pady=5)
        tb.Button(caption_frame,text="💧 Watermark",command=self.pick_watermark, bootstyle="success-outline").grid(row=1,column=0,pady=5)
        tb.Button(caption_frame,text="🎵 Chọn nhạc",command=self.pick_music, bootstyle="info-outline").grid(row=1,column=1,pady=5)
        tb.Button(caption_frame,text="🎬 Intro/Outro",command=self.pick_intro_outro, bootstyle="warning-outline").grid(row=1,column=2,pady=5)

        # --- Process card ---
        process_frame = tb.Labelframe(main_frame, text="3. Tải & Chỉnh sửa + Crop", padding=10, bootstyle="primary")
        process_frame.pack(fill='x', pady=5)
        tb.Button(process_frame,text="⬇️ Tải & Edit + Crop",command=self.download_edit_crop, bootstyle="success").grid(row=0,column=0, padx=5, pady=5)
        tb.Button(process_frame,text="⬆️ Upload TikTok",command=self.upload_video, bootstyle="primary").grid(row=0,column=1, padx=5, pady=5)
        self.status = tb.Label(process_frame, text="Ready", foreground="blue")
        self.status.grid(row=1,column=0,columnspan=2, sticky='w', pady=5)

        # Progress bar
        self.progress = tb.Progressbar(process_frame, mode='indeterminate', bootstyle="info-striped", length=500)
        self.progress.grid(row=2,column=0,columnspan=2, pady=5)

        # Init vars
        self.watermark = None
        self.music = None
        self.intro = None
        self.outro = None
        self.last_output = None

    # ---------- Hàm xử lý ----------
    def set_status(self,text):
        self.status.config(text=text)
        self.root.update_idletasks()

    def show_wait_dialog(self, text="Vui lòng chờ..."):
        self.wait_win = tb.Toplevel(self.root)
        self.wait_win.title("Đang xử lý")
        self.wait_win.geometry("300x90")
        self.wait_win.transient(self.root)
        self.wait_win.grab_set()
        tb.Label(self.wait_win, text=text, font=("Arial", 12)).pack(pady=10)
        pb = tb.Progressbar(self.wait_win, mode='indeterminate', bootstyle="info-striped", length=250)
        pb.pack(pady=5)
        pb.start()
        self.wait_pb = pb

    def close_wait_dialog(self):
        if hasattr(self, 'wait_win'):
            self.wait_pb.stop()
            self.wait_win.destroy()

    def on_search(self):
        q = self.query_var.get().strip()
        if not q:
            messagebox.showwarning("Cần từ khóa","Nhập từ khóa để tìm video")
            return

        self.progress.start()
        self.set_status("Đang tìm kiếm theo từ khóa...")

        def worker():
            try:
                results = search_youtube(q, max_results=15)
                self.results = results
                self.listbox.delete(0, tk.END)
                for r in results:
                    self.listbox.insert(tk.END, f"{r['title']} [{r['duration']//60}:{r['duration']%60:02d}] ({r['view_count']})")
                if results:
                    self.listbox.selection_set(0)
                    self.update_thumbnail()
                self.set_status(f"Found {len(results)} results")
            except Exception as e:
                self.set_status(f"Lỗi: {e}")
            finally:
                self.progress.stop()

        threading.Thread(target=worker, daemon=True).start()

    def preview(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Chọn video","Chọn video trước")
            return
        idx = sel[0]
        url = self.results[idx]['url']
        webbrowser.open(url)
        self.set_status("Opened preview in browser")

    def update_thumbnail(self, event=None):
        sel = self.listbox.curselection()
        if not sel or not self.results:
            return
        idx = sel[0]
        thumb_url = self.results[idx]['thumbnail']
        img = fetch_thumbnail(thumb_url)
        if img:
            self.thumbnail_img = img
            self.thumbnail_label.config(image=self.thumbnail_img)

    def pick_watermark(self):
        p = filedialog.askopenfilename(filetypes=[("Image","*.png;*.jpg;*.jpeg;*.webp")])
        if p:
            self.watermark = p
            self.set_status(f"Watermark: {os.path.basename(p)}")

    def pick_music(self):
        p = filedialog.askopenfilename(filetypes=[("Audio","*.mp3;*.wav;*.m4a")])
        if p:
            self.music = p
            self.set_status(f"Music: {os.path.basename(p)}")

    def pick_intro_outro(self):
        p = filedialog.askopenfilename(title="Chọn Intro (Cancel nếu bỏ)",filetypes=[("Video","*.mp4;*.mov;*.mkv")])
        if p:
            self.intro = p
        q = filedialog.askopenfilename(title="Chọn Outro (Cancel nếu bỏ)",filetypes=[("Video","*.mp4;*.mov;*.mkv")])
        if q:
            self.outro = q
        self.set_status("Intro/Outro set")

    def download_edit_crop(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Chọn video","Chọn video trước")
            return
        idx = sel[0]
        url = self.results[idx]['url']
        caption = self.caption_text.get("1.0","end").strip()
        outdir = filedialog.askdirectory(title="Chọn thư mục lưu file")
        if not outdir: return
        temp_dir = tempfile.mkdtemp(prefix="yt2tk_")
        self.show_wait_dialog("Downloading & Editing Video...")

        def worker():
            try:
                outtmpl = os.path.join(temp_dir,"%id%.%(ext)s")
                info = download_video(url, os.path.join(temp_dir,"%(id)s.%(ext)s"))
                video_id = info['id']
                candidates = [os.path.join(temp_dir,f) for f in os.listdir(temp_dir)]
                video_file = None
                for c in candidates:
                    if c.endswith(".mp4") or c.endswith(".mkv") or c.endswith(".webm"):
                        video_file = c
                        break
                if not video_file:
                    video_file = outtmpl.replace("%id%", video_id).replace("%ext%","mp4")
                edited_path = os.path.join(outdir,f"{video_id}_edited.mp4")
                edit_video(video_file, edited_path, caption_text=caption,
                           watermark_path=self.watermark, music_path=self.music,
                           intro_path=self.intro, outro_path=self.outro)
                cropped_path = os.path.join(outdir,f"{video_id}_9x16.mp4")
                crop_16_9_to_9_16(edited_path, cropped_path)
                self.last_output = cropped_path
                self.set_status(f"Done: {cropped_path}")
                messagebox.showinfo("Hoàn tất", f"File xuất: {cropped_path}")
            except Exception as e:
                self.set_status(f"Lỗi: {e}")
            finally:
                self.close_wait_dialog()

        threading.Thread(target=worker, daemon=True).start()

    def upload_video(self):
        if not self.last_output:
            messagebox.showinfo("Chọn video","Chưa có video để upload")
            return
        caption = self.caption_text.get("1.0","end").strip()
        self.show_wait_dialog("Uploading to TikTok (demo)...")

        def worker():
            try:
                video_id = upload_to_tiktok(self.last_output, caption)
                self.set_status(f"Uploaded video id: {video_id}")
                messagebox.showinfo("Upload", f"Demo upload xong! Video id: {video_id}")
            finally:
                self.close_wait_dialog()


if __name__ == "__main__":
    root = tb.Window(themename="litera")  # theme sáng
    app = App(root)
    root.mainloop()
