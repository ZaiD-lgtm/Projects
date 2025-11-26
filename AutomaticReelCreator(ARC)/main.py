import json
import os
import random
import Gen_and_cut
import CAPTION
import yt_calls
import video_processing_and_upload_code
import time
import csv
import yaml
import generate_time_schedule
import yaml_edit
import youtube_transcript

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

filename = config["clear_csv"]

while True:
    yaml_file = 'config.yaml'

    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)
        token = data["token"]
        search = data["search"]
        description = data["description"]

    directory = "trimmed_videos"
    has_files = any(os.path.isfile(os.path.join(directory, f)) for f in os.listdir(directory))

    if not has_files:
        token, search, description = yaml_edit.choose_token_caption()
        print(f"token: {token} || searching: {search}")

        yaml_file = 'config.yaml'
        yaml_edit.change_yaml_key(yaml_file, ['token'], token)
        yaml_edit.change_yaml_key(yaml_file, ['search'], search)
        yaml_edit.change_yaml_key(yaml_file, ['description'], description)
        # Verify the changes
        print("\n--- Updated YAML content ---")

        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
            token = data["token"]
            search = data["search"]
            description = data["description"]

        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
        print(f"Cleared: {filename}")
        print("no files!")
        print(os.listdir(directory))
        picked_video_info = yt_calls.yt_call(search, 10)
        link = picked_video_info[0]
        video_id = picked_video_info[1]
        iso_duration_video = picked_video_info[2]
        duration_seconds = picked_video_info[3]

        transcripts = youtube_transcript.get_transcript(video_id=video_id)
        prompt = '''
            From the following transcript: {transcripts}, identify multiple engaging, interesting, or dramatic segments suitable for YouTube Shorts clips.

        For each identified segment, generate a concise and catchy caption.

        Your entire response MUST be a single Python list.
        Each element within this main list MUST be a sub-list.
        Each sub-list MUST contain exactly three elements, in this precise order:
        1.  The start timestamp of the segment (as a string, e.g., 'HH:MM:SS').
        2.  The end timestamp of the segment (as a string, e.g., 'HH:MM:SS').
        3.  The suitable and catchy caption for that segment (as a single string).

        Do NOT include any additional elements, text, comments (lines starting with #), or explanations outside or inside the list structure.
        Each segment should be at least 30 seconds long and a maximum of 60 seconds long.
        Segments must end cleanly at a natural sentence or event boundary and must not cut off abruptly.

        Example of desired output format:
        [
          ['00:00:00', '00:00:35', 'Epic moment: Player pulls off an insane trick shot!'],
          ['00:01:10', '00:01:50', 'Unexpected twist as the story takes a dark turn.'],
          ['00:02:30', '00:03:00', 'Hilarious fail compilation from the live stream.']
        ]
            '''
        print("Script execution started.")
        video_counter = 1
        timelines, captions = Gen_and_cut.generate(link=link, prompt=prompt,base_video_filename="my_downloaded_video")
        # text_list = json.loads(text_list)
        print("======================================================================================")
        print("timelines: ",timelines)
        print("======================================================================================")
        print("Captions: ", captions)
        grouped_pairs = []
        for i in range(0, len(timelines), 2):
            if i + 1 < len(timelines):
                grouped_pairs.append([timelines[i], timelines[i + 1]])
            else:
                pass
        num_videos = len(grouped_pairs)
        print("Grouped Pairs: ", grouped_pairs)
        print(f"{num_videos} videos!")
        # print(grouped_pairs)
        num_videos = len(grouped_pairs)
        print(f"Generating {num_videos} random ISO times with gaps between 45 minutes and 2 hours:")
        times = generate_time_schedule.generate_random_iso_times(num_videos)
        print("Times: ", times)

        if not times:
            print("Scheduled time not found")
        list_time_schedule = []  #to schedule videos, ISO future times will be stored in this list

        for i, t in enumerate(times):
            list_time_schedule.append(t)
            print(f"Time {i + 1}: {t}")
        list_time_schedule = list_time_schedule[::-1]  #reverse the list so that nearset time can be accessed using pop function.

        yaml_file = 'config.yaml'
        yaml_edit.change_yaml_key(yaml_file, ['schedule_time'], list_time_schedule)

        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
            list_time_schedule = data["schedule_time"]


        for i in grouped_pairs:
            output_path = f"trimmed_videos/t_video_{video_counter}.mp4"
            start_time = i[0]
            end_time = i[-1]
            duration = Gen_and_cut.get_duration(start_time, end_time)
            Gen_and_cut.trim_video("my_downloaded_video.mp4", output_path, start_time, duration)
            text = f"{start_time} to {end_time}"
            # prompt_cap = f'''Give me the single best caption for this video inside a python list of string. eg: ["caption"]'''
            # caption_list = CAPTION.generate_caption(link, prompt_cap)
            # caption_list = json.loads(caption_list)
            with open("picked_caption.csv", mode='a', newline='', encoding='utf-8') as file:
                caption = captions[video_counter-1]
                writer = csv.writer(file)
                writer.writerow([f"video{video_counter}|||{caption}"])
            print(f"Chose caption {caption} for video{video_counter}")
            video_counter += 1
            print(f"text_list len: {len(captions)}")
        os.remove("my_downloaded_video.mp4")
        # os.remove("my_downloaded_video")
        print(f"token: {token}")

        fixed_schedule_time = list_time_schedule.pop()
        yaml_edit.change_yaml_key(yaml_file, ['schedule_time'], list_time_schedule)

        input_video_path, new_video_path = video_processing_and_upload_code.video_processing_and_upload(token,fixed_schedule_time)

        os.remove(input_video_path)
        # os.remove(new_video_path)
    else:

        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
            list_time_schedule = data["schedule_time"]

        fixed_schedule_time = list_time_schedule.pop()
        yaml_edit.change_yaml_key(yaml_file, ['schedule_time'], list_time_schedule)

        input_video_path, new_video_path = video_processing_and_upload_code.video_processing_and_upload(token,fixed_schedule_time)
        os.remove(input_video_path)
    time.sleep(60)

print("Program Finished")