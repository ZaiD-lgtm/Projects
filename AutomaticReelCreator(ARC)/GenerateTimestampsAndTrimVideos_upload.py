import ast

import ffmpeg
import os
import json
from datetime import datetime
import yt_dlp
# from google import generativeai
import yt_calls
# import CAPTION
import requests
# load_dotenv()


API_KEY = os.getenv("api_key_gemini")
if not API_KEY:
    raise ValueError("api key environment variable not set. set it before running.")

def get_duration(start, end):
    try:
        FMT = "%H:%M:%S"
        tdelta = datetime.strptime(end, FMT) - datetime.strptime(start, FMT)
    except ValueError:
        FMT = "%M:%S"
        tdelta = datetime.strptime(end, FMT) - datetime.strptime(start, FMT)
    return str(tdelta)


def download_video(youtube_url, output_filename_base="downloaded_video"):
    output_filename = f"{output_filename_base}.mp4"

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_filename,
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': False,
        'overwrites': True,
    }

    print(f"Attempting to download video from {youtube_url} to {output_filename}...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=True)
            downloaded_filepath = info_dict.get('filepath') or ydl.prepare_filename(info_dict)

            if downloaded_filepath:
                print(f"Video downloaded successfully to: {downloaded_filepath}")
                return downloaded_filepath
            else:
                print("yt-dlp completed, but could not determine downloaded file path.")
                return None
    except yt_dlp.DownloadError as e:
        print(f"Error downloading video: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during video download: {e}")
        return None


def generate(link, prompt,base_video_filename="downloaded_video"):
    download_video(link, base_video_filename)
    print(f"Starting generate function for link: {link}, base filename: {base_video_filename}")
    global mistral_response

    timelines = []
    captions = []

    API_KEY = ""
    url = "https://api.mistral.ai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistral-small",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=payload)

    try:
        response.raise_for_status()
        data = response.json()
        if "choices" in data:
            mistral_response_string = data["choices"][0]["message"]["content"]
            mistral_parsed_list = ast.literal_eval(mistral_response_string)
            print(f"Mistral Response: {mistral_parsed_list}")
            for item in mistral_parsed_list:
                timelines.extend(item[:2])
                captions.append(item[2])
        else:
            print("Unexpected response:", data)
    except requests.exceptions.HTTPError as e:
        print("HTTP Error:", e)
        print("Response Text:", response.text)
    except Exception as e:
        print("Unexpected Error:", e)
        print("Raw Response:", response.text)


    return timelines, captions


def trim_video(input_path, output_path, start_time, duration):
    print(f"\n--- Starting Video Trimming ---")
    print(f"Input Video Path: '{input_path}'")
    print(f"Output Video Path: '{output_path}'")
    print(f"Trim Start Time: {start_time}")
    print(f"Trim Duration: {duration}")

    # try:
    if os.system("where ffmpeg > nul 2>&1") != 0: # Checks if ffmpeg is found in PATH
        print("FFmpeg not found in system PATH. Please ensure FFmpeg is installed and added to your system's PATH.")
        return

    if not os.path.exists(input_path):
        print(f"Error: Input video file '{input_path}' does not exist. Please check the path.")
        return

    cmd = ffmpeg.input(input_path, ss=start_time).output(output_path, t=str(duration), vcodec='libx264',
                                                          acodec='aac')

    cmd.run(overwrite_output=True)

    print(
        f"Video trimmed successfully: '{input_path}' from {start_time} for a duration of {duration} -> '{output_path}'")
    print(f"--- Video Trimming Complete ---\n")



if __name__ == "__main__":
    video_counter = 1
    print("Script execution started.")

    text_list = generate("https://youtu.be/L0AFgRUvNis?si=EEKj3atNzikxZXV1", "my_downloaded_video")
    text_list = json.loads(text_list)
    print("======================================================================================")
    print(text_list)
    grouped_pairs = []
    for i in range(0, len(text_list), 2):
        if i + 1 < len(text_list):
            grouped_pairs.append([text_list[i], text_list[i + 1]])
        else:
            pass
    print(grouped_pairs)
    caption_list = []
    for i in grouped_pairs:
        output_path = f"trimmed_videos/t_video_{video_counter}.mp4"
        start_time = i[0]
        end_time = i[-1]
        duration = get_duration(start_time, end_time)
        trim_video("my_downloaded_video.mp4", output_path, start_time, duration)
        video_counter += 1
    print(f"text_list len: {len(text_list)}")
    print("Script execution finished.")
