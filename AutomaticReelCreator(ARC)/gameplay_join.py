import ffmpeg
import random

def trim_video_gameplay_only(input_path, output_path,end_time=None,duration = None):
    try:
        mm = random.randint(0,29)
        ss = random.randint(0,30)
        if 0<=mm<=9:
            mm = f"0{mm}"
        if 0<=ss<=9:
            ss = f"0{ss}"

        start_time = f"00:{mm}:{ss}"
        (
            ffmpeg
            .input(input_path, ss=start_time)
            .output(output_path, t=duration, vcodec='libx264', acodec='aac')
            .run(overwrite_output=True)
        )
        if duration == None:
            print(f"Video trimmed successfully: '{input_path}' from {start_time} to {end_time} -> '{output_path}'")
        else:
            print(f"Video trimmed successfully: '{input_path}' from {start_time} to for the duration of {duration}'")
    except ffmpeg.Error as e:
        print(f"An FFmpeg error occurred: {e.stderr.decode()}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def join_gameplay_with_sections(input_short_path, input_gameplay_path, output_path="output_final.mp4"):
    input_short = ffmpeg.input(input_short_path)

    input_gameplay = ffmpeg.input(input_gameplay_path)
    short_scaled = input_short.video.filter('scale', 1080, 1248)
    gameplay_scaled = input_gameplay.video.filter('scale', 1080, 672)

    stacked_video = ffmpeg.filter([short_scaled, gameplay_scaled], 'vstack')

    stacked_with_audio = ffmpeg.output(
        stacked_video, input_short.audio,  # original audio
        output_path,
        vcodec='libx264',
        acodec='aac',
        shortest=None,
        format='mp4'
    )

    stacked_with_audio.run(overwrite_output=True)
    print(f"Final Shorts-style video generated: {output_path}")

if __name__ == "__main__":
    trim_video_gameplay_only("minecraft_gameplay.mp4", "output_gameplay.mp4", duration= 30)
    join_gameplay_with_sections("t_video_1.mp4", "output_gameplay.mp4", "with_gameplay.mp4")

