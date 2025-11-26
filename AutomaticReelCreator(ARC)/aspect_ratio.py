import ffmpeg
import os

def convert_to_shorts_format(input_video, output_video, target_width=1080, target_height=1920):
    if not os.path.exists(input_video):
        print(f"Error: Input video file '{input_video}' not found.")
        return

    try:
        probe = ffmpeg.probe(input_video)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        in_width = int(video_stream['width'])
        in_height = int(video_stream['height'])

        in_aspect = in_width / in_height
        target_aspect = target_width / target_height

        if in_aspect > target_aspect:
            new_width = int(in_height * target_aspect)
            x_offset = int((in_width - new_width) / 2)
            crop_filter = f"crop={new_width}:{in_height}:{x_offset}:0"
        else:
            new_height = int(in_width / target_aspect)
            y_offset = int((in_height - new_height) / 2)
            crop_filter = f"crop={in_width}:{new_height}:0:{y_offset}"

        print(f"Applying: {crop_filter}, scaling to {target_width}x{target_height}")

        video = (
            ffmpeg
            .input(input_video)
            .filter('crop', *[int(val) for val in crop_filter.split('=')[1].split(':')])
            .filter('scale', target_width, target_height)
            .filter('setsar', '1')
        )

        audio = ffmpeg.input(input_video).audio

        (
            ffmpeg
            .output(video, audio, output_video, vcodec='libx264', acodec='copy', strict='experimental')
            .overwrite_output()
            .run(capture_stderr=True)
        )

        print(f"✅ Converted to Shorts format (with audio preserved): {output_video}")

    except ffmpeg.Error as e:
        print(f"FFmpeg error: {e.stderr.decode('utf-8')}")
    except Exception as e:
        print(f"Unexpected error: {e}")
if __name__ == "__main__":
    convert_to_shorts_format("t_video_1.mp4", "t_video_1_new.mp4")
