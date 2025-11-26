import ffmpeg
import os
import datetime
import random
def web_to_ass_color(web_color):
    if web_color.startswith("#"):
        r = int(web_color[1:3], 16)
        g = int(web_color[3:5], 16)
        b = int(web_color[5:7], 16)
        return f"&H00{b:02X}{g:02X}{r:02X}"
    return web_color


def burn_subtitles_into_video(video_path, srt_path, output_path,
                              font_size=40, font_color="white",
                              font_style = None,
                              text_outline_color="black", text_outline_width=2,
                              position_bottom_padding=25):
    list = ["Arial Rounded MT Bold", "Bebas Neue", "Berlin Sans FB", "Bernard MT Condensed", "Bookman Old Style",
            "Britannic Bold", "Carlito", "Cosmic Sans MS", "Copper Black", "Impact", "Kristen ITC", "Luckiest Guy",
            "Rockwell Bold", "Showcard Gothic", "Super Lobster", "Verdana"]
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found.")
        return
    if not os.path.exists(srt_path):
        print(f"Error: SRT file '{srt_path}' not found. Please ensure it's generated first.")
        return

    ffmpeg_srt_path = srt_path.replace(os.sep, '/')

    ass_primary_color = web_to_ass_color(font_color)
    ass_outline_color = web_to_ass_color(text_outline_color)

    style_params = [
        f"FontSize={font_size}",
        f"PrimaryColour={ass_primary_color}",
        f"OutlineColour={ass_outline_color}",
        f"Outline={text_outline_width}",
        f"MarginV={position_bottom_padding}"
    ]
    if font_style is None:
        font_style = random.choice(list)
        style_params.insert(0, f"Fontname={font_style}")
        force_style_str = ','.join(style_params)
    else:
        style_params.insert(0, f"Fontname={font_style}")
        force_style_str = ','.join(style_params)

    subtitle_filter = f"subtitles='{ffmpeg_srt_path}':force_style='{force_style_str}'"

    print(f"FFmpeg subtitle filter command: {subtitle_filter}")

    try:
        (
            ffmpeg
            .input(video_path)
            .output(output_path, vf=subtitle_filter)
            .run(overwrite_output=True, capture_stderr=True)
        )
        print(f"Subtitles burned successfully into '{output_path}'")
    except ffmpeg.Error as e:
        print(f"An FFmpeg error occurred: {e.stderr.decode('utf-8')}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    input_video_file = "t_video_1_new.mp4"
    generated_srt_file = "output_subtitles.ass"

    output_directory = "final_videos_with_subtitles"
    os.makedirs(output_directory, exist_ok=True)
    final_output_video = os.path.join(output_directory, "video_with_burned_subs.mp4")

    if not os.path.exists(input_video_file):
        print(f"Error: Input video file '{input_video_file}' not found. Please provide a valid path.")
        exit()

    if not os.path.exists(generated_srt_file):
        print(f"Error: Generated SRT file '{generated_srt_file}' not found. Please ensure it's generated first.")
        exit()

    FONT_CHOICES = [
        "Arial Rounded MT Bold",
        "Bebas Neue",
        "Berlin Sans FB",
        "Bernard MT Condensed",
        "Bookman Old Style",
        "Britannic Bold",
        "Carlito",
        "Comic Sans MS",
        "Copperplate Gothic Bold",
        "Kristen ITC",
        "Luckiest Guy",
        "Rockwell Bold",
        "Showcard Gothic",
        "Lobster",
        "Verdana"
    ]

    COLOR_CHOICES = [
        "#FFFFFF",  # White
        "#FFFF00",  # Yellow
        "#00FFFF",  # Cyan
        "#00FF00",  # Green
        "#FFA500",  # Orange
        "#C0C0C0",  # Silver (light gray)
        "#FFC0CB",  # Pink
        "#008080",  # Teal,
        "#FFFFFF",  # White
        "#FFFFE0",  # Light Yellow
        "#FFFACD",  # Lemon Chiffon (another light yellow)
        "#ADD8E6",  # Light Blue
        "#90EE90",  # Light Green
        "#FFC0CB",  # Pink
        "#C0C0C0",  # Silver (light gray)
        "#E0FFFF",  # Pale Turquoise
        "#F0FFFF",  # Azure (very light blue)
        "#F5FFFA",  # Mint Cream (very light green/white)
        "#FFE4B5",  # Moccasin (pale orange/peach)
        "#F5F5DC",  # Beige (can work as light)
        "#FFF8DC",  # Cornsilk (off-white/light yellow)
        "#808080",  # Gray (Medium Gray)
        "#4682B4",  # Steel Blue (Muted Blue)
        "#5F9EA0",  # Cadet Blue (Muted Cyan-Blue)
        "#6B8E23",  # Olive Drab (Muted Green-Brown)
        "#CD5C5C",  # Indian Red (Muted Red)
        "#B8860B",  # Dark Goldenrod (Muted Gold/Brown)
        "#DAA520",  # Goldenrod (Brighter Gold)
        "#A0522D",  # Sienna (Earthy Brown)
        "#8B4513",  # Saddle Brown (Darker Brown)
        "#8A2BE2",  # Blue Violet (Muted Purple)
        "#483D8B",  # Dark Slate Blue (Deep Muted Blue)
        "#20B2AA",  # Light Sea Green (Muted Teal)
        "#696969",  # Dim Gray (Slightly darker medium gray)
        "#708090",  # Slate Gray (Bluish-gray)
    ]
    chosen_font_name = random.choice(FONT_CHOICES)
    chosen_font_color = random.choice(COLOR_CHOICES)

    base_path_fonts = "C:/Users/Administrator/main/ARC/selected"
    ttf_file_name = "Kablammo[MORF]"
    my_custom_font_path = os.path.join(base_path_fonts,ttf_file_name)

    burn_subtitles_into_video(
        input_video_file,
        generated_srt_file,
        final_output_video,
        font_style= chosen_font_name,
        font_size=40,
        font_color=chosen_font_color,
        text_outline_color="#000000",
        text_outline_width=8,
        position_bottom_padding=400
    )

    print(f"\nYour video with burned-in subtitles is at: {final_output_video}")
    print("Remember to customize the 'input_video_file', 'generated_srt_file', and 'my_custom_font_path' paths.")