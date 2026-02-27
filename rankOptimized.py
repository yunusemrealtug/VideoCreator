import os
from moviepy import ImageClip, TextClip, CompositeVideoClip, ColorClip, AudioFileClip
import json
from PIL import Image
import numpy as np
import re

year = "BestPicture"
# JSON dosyası
with open("datas/top100" + year +".json", "r", encoding="utf-8") as f:
    data = json.load(f)

# === CONFIG ===
POSTER_PATH = "posters/posters"+ year +"s"  # posterlerin bulunduğu klasör
VIDEO_SIZE = (1920, 1080)
FPS = 60
DURATION_PER_MOVE = 4  # her hareketin süresi (saniye)
OUTPUT_FILE = "poster_gallery.mp4"
intro_duration = 5  # saniye
poster_width = VIDEO_SIZE[0] // 4
poster_height = VIDEO_SIZE[0] // 3
GAP = 20  # posterler arasındaki boşluk (piksel)
bgColor = (212, 175, 55)
textString = year + " Winners Ranked Based on IMDB Score and Metascore"
intro_bg = ColorClip(size=VIDEO_SIZE, color=bgColor).with_duration(intro_duration)
music = AudioFileClip("themes/theme22.mp3")

# Veriler
game_names = [game["title"] for game in data]
year = [game["year"] for game in data]
developer = [game["developer"] for game in data]
score = [game["score"] for game in data]
second = [game["second"] for game in data]
third = [game["third"] for game in data]
fourth = [game["fourth"] for game in data]
# === FOTOLAR ===
def natural_key(string):
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r"(\d+)", string)]

image_files = sorted(
    [
        os.path.join(POSTER_PATH, f)
        for f in os.listdir(POSTER_PATH)
        if f.lower().endswith((".jpg","jpeg", ".png"))
    ],
    key=natural_key,
    reverse=True
)

num_images = len(image_files)
if num_images < 3:
    raise ValueError("En az 3 poster olmalı.")


clips = []

intro_text = TextClip(
    text=textString,
    font="C:\\Windows\\Fonts\\candara.ttf",
    font_size=100,
    color="white",
    method="caption",
    size=(1500, 200)
).with_position("center").with_duration(intro_duration)


clips.append(intro_text)


for i, img_path in enumerate(image_files):

    start_time = i*DURATION_PER_MOVE + intro_duration
    visible_duration = 5 * DURATION_PER_MOVE
    if (i+4>num_images):
        visible_duration = (num_images-1-i)*DURATION_PER_MOVE+visible_duration-7
    
    img = Image.open(img_path)

    if "icc_profile" not in img.info or img.mode != "RGB":
        img = img.convert("RGB")

    clip = ImageClip(np.array(img)).resized(new_size=(poster_width, poster_height)).without_mask()

    def position(t, i=i):
        x = VIDEO_SIZE[0] - (poster_width + GAP) * (t / DURATION_PER_MOVE)
        if ((i + 4) > num_images):
            x = max (x, ((i-97)*(poster_width + GAP)+GAP))
        if x + poster_width <= 0:
            x = -poster_width
        elif x >= VIDEO_SIZE[0]:
            x = VIDEO_SIZE[0]
        y_offset = 100  # ekranın biraz üstünde olsun
        return x, (VIDEO_SIZE[1] - clip.h) / 2 - y_offset

    # === Poster Akisi ===
    moving_clip = clip.with_position(lambda t, i=i: position(t, i)).with_duration(visible_duration).with_start(start_time)

    clips.append(moving_clip)

    # === Icerik ===
    year_text = os.path.splitext(os.path.basename(img_path))[0]
    game_names_text = game_names[i]
    developer_text = developer[i]
    score_text = score[i]
    second_text = second[i]
    third_text = third[i]
    fourth_text = fourth[i]

    year_clip = TextClip(
        font="C:\\Windows\\Fonts\\candara.ttf", 
        text=year_text,
        font_size=40,
        color="white",
        method="caption",
        size=(poster_width//3, 100),
        bg_color=(0,0,0,1)
    ).without_mask()

    score_clip = TextClip(
        font="C:\\Windows\\Fonts\\candara.ttf", 
        text=score_text,
        font_size=40,
        color="white",
        method="caption",
        size=(poster_width//4, 100),
        bg_color=(0,202,126, 1)
    ).without_mask()

    game_names_clip = TextClip(
        font="C:\\Windows\\Fonts\\candara.ttf",  
        text=game_names_text,
        font_size=min(50, 900//len(game_names_text)),
        color="white",
        method="caption",
        size=(poster_width, 80),
        bg_color=(0,0,0,1),

    ).without_mask()


    developer_clip = TextClip(
        font="C:\\Windows\\Fonts\\candara.ttf", 
        text=developer_text,
        font_size=min(30, 950//len(developer_text)),
        color="white",
        method="caption",
        size=(poster_width, 60),
        bg_color=(0,0,0,1),
    ).without_mask()

    second_clip = TextClip(
        font="C:\\Windows\\Fonts\\candara.ttf",
        text=second_text,
        font_size=min(25, 950//len(second_text)),
        color="white",
        method="caption",
        size=(poster_width, 40),
        bg_color=(0,0,0,1),
    ).without_mask()

    third_clip = TextClip(
        font="C:\\Windows\\Fonts\\candara.ttf", 
        text=third_text,
        font_size=min(25, 950//len(third_text)),
        color="white",
        method="caption",
        size=(poster_width, 40),
        bg_color=(0,0,0,1),
    ).without_mask()

    fourth_clip = TextClip(
        font="C:\\Windows\\Fonts\\candara.ttf", 
        text=fourth_text,
        font_size=min(25, 950//len(fourth_text)),
        color="white",
        method="caption",
        size=(poster_width, 40),
        bg_color=(0,0,0,1),
    ).without_mask()
  
    def year_position(t, i=i):
        x = VIDEO_SIZE[0] - (poster_width + GAP) * (t / DURATION_PER_MOVE)
        if ((i + 4) > num_images):
            x = max (x, ((i-97)*(poster_width + GAP) + GAP))
        if x + poster_width//3 <= 0:
            x = -poster_width//3
        elif x >= VIDEO_SIZE[0]:
            x = VIDEO_SIZE[0]
        
        return x, 20

    def score_position(t, i=i):
        x = VIDEO_SIZE[0] + (poster_width+GAP)*0.72 - (poster_width + GAP) * (t / DURATION_PER_MOVE)
        if ((i + 4) > num_images):
            x = max (x, (i-97)*(poster_width + GAP) + (poster_width+GAP)*0.72 + GAP)
        if x + poster_width//4 <= 0:
            x = -poster_width//4
        elif x >= VIDEO_SIZE[0]:
            x = VIDEO_SIZE[0]
        return x, 20

    def title_position(t, i=i):
        x, y = position(t, i)
        return x, y + clip.h + 20 


    def director_position(t, i=i):
        x, y = position(t, i)
        return x, y + clip.h + 100 

    def actor_position_1(t, i=i):
        x, y = position(t, i)
        return x, y + clip.h + 160 

    def actor_position_2(t, i=i):
        x, y = position(t, i)
        return x, y + clip.h + 200 

    def actor_position_3(t, i=i):
        x, y = position(t, i)
        return x, y + clip.h + 240 


    moving_year = year_clip.with_position(lambda t, i=i: year_position(t, i)).with_duration(visible_duration).with_start(start_time)
    moving_title = game_names_clip.with_position(lambda t, i=i: title_position(t, i)).with_duration(visible_duration).with_start(start_time)
    moving_score = score_clip.with_position(lambda t, i=i: score_position(t, i)).with_duration(visible_duration).with_start(start_time)
    moving_director = developer_clip.with_position(lambda t, i=i: director_position(t, i)).with_duration(visible_duration).with_start(start_time)
    moving_actor1 = second_clip.with_position(lambda t, i=i: actor_position_1(t, i)).with_duration(visible_duration).with_start(start_time)
    moving_actor2 = third_clip.with_position(lambda t, i=i: actor_position_2(t, i)).with_duration(visible_duration).with_start(start_time)
    moving_actor3 = fourth_clip.with_position(lambda t, i=i: actor_position_3(t, i)).with_duration(visible_duration).with_start(start_time)


    clips.append(moving_year)
    clips.append(moving_title)
    clips.append(moving_score)
    clips.append(moving_director)
    clips.append(moving_actor1)
    clips.append(moving_actor2)
    clips.append(moving_actor3)

final = CompositeVideoClip(clips, size=VIDEO_SIZE)
background = ColorClip(size=VIDEO_SIZE, color=bgColor).with_duration(final.duration)
final = CompositeVideoClip([background, *clips], size=VIDEO_SIZE)



music = music.subclipped(0, final.duration)
final = final.with_audio(music)
final.write_videofile(
    OUTPUT_FILE,
    fps=FPS,
    codec="libx264",
    audio_codec="aac", 
    preset="medium",
    bitrate="4000k",
)
