import os
import random
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
import csv
import yaml

def change_yaml_key(file_path, keys, new_value):
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)

        if data is None:
            data = {}  # Initialize an empty dictionary if the file is empty or malformed

        # Traverse the dictionary to find the target key
        current_level = data
        for i, key in enumerate(keys):
            if key not in current_level:
                print(f"Warning: Key '{key}' not found at this level. Creating it.")
                current_level[key] = {} if i < len(keys) - 1 else None # Create nested dict if not last key
            if i < len(keys) - 1:
                current_level = current_level[key]
            else:
                current_level[key] = new_value

        with open(file_path, 'w') as file:
            yaml.safe_dump(data, file, default_flow_style=False, sort_keys=False)
        print(f"Successfully updated '{'->'.join(keys)}' in '{file_path}' to '{new_value}'.")

    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
    except yaml.YAMLError as e:
        print(f"Error parsing or writing YAML file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def choose_token_caption():
    global description
    dict_tokens = {
        0: "go random!",
        1: ["tokens/football_token.json", "Epic Football Moments with Commentary", "#Shorts #shorts #shortsfeed #shortsvideo #shortsviral #shortsyoutube #football #footballshorts #footballskills #fun #footballedits #footballhighlights #footballer #trending #viral"],
        2: ["tokens/glam_token.json", "Raj Shamani Podcast", "#Shorts #shorts #shortsfeed #shortsvideo #shortsviral #shortsyoutube #rajshamani #podcast #podcastclips #podcasts #fun #trending #viral  "],
        3: ["tokens/speed_token.json", "I Show Speed Stream", "#Shorts #shorts #shortsfeed #shortsvideo #shortsviral #shortsyoutube #ishowspeed #ishowspeedshorts #ishowspeedclips #ishowspeedmemes #fun #ishowspeedmoments #trending #viral"],
        4: ["tokens/talk_show_token.json", "night show", "#Shorts #shorts #shortsfeed #shortsvideo #shortsviral #shortsyoutube #tonightshow #nightshow #tonightshowshorts #jimmyfallon #fun #trending #viral"],
        5: ["tokens/twitch_rewind_token.json", "twitch clips", "#Shorts #shorts #shortsfeed #shortsvideo #shortsviral #shortsyoutube #twitch #twitchstreamer #twitchclips #twitchtv #twitchgaming #twitchstream #twitchhighlights #twitchmoments #fun #trending #viral"]
    }
    print('''
    0: go random!
    1: football_token.json
    2: glam_token.json
    3: speed_token.json
    4: talk_show_token.json
    5: twitch_rewind_token.json
    ''')
    inp = int(input("Choose one of the options: "))
    list = [0, 1, 2, 3, 4, 5]
    if inp in list:
        if inp != 0:
            token = dict_tokens[inp][0]
            search = dict_tokens[inp][1]
            description = dict_tokens[inp][2]
        else:
            inp = random.choice(list)
            token = dict_tokens[inp][0]
            search = dict_tokens[inp][1]
            description = dict_tokens[inp][2]
    else:
        print("Wrong Input!. Try Again >>>>")
        token, search = choose_token_caption()

    return token, search, description
if __name__ == "__main__":
    token, search, description = choose_token_caption()
    print(f"token: {token} || searching: {search}")

    yaml_file = 'config.yaml'
    change_yaml_key(yaml_file, ['token'], token)
    change_yaml_key(yaml_file, ['search'], search)
    change_yaml_key(yaml_file,['description'],description)
    # Verify the changes
    print("\n--- Updated YAML content ---")
    # with open(yaml_file, 'r') as f:
    #     data = yaml.safe_load(f)
    #     print(data["token"])
    #     print(data["search"])
