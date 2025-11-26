from googleapiclient.discovery import build

api_key = ""
def yt_call(search_query,max):

    youtube = build('youtube', 'v3', developerKey=api_key)


    # Search request
    search_request = youtube.search().list(
        q=search_query,
        part="snippet",
        type="video",
        maxResults=max,
    )
    search_response = search_request.execute()

    video_ids = [item['id']['videoId'] for item in search_response['items']]


    details_request = youtube.videos().list(
        part="contentDetails",
        id=",".join(video_ids)
    )
    details_response = details_request.execute()


    durations = {item['id']: item['contentDetails']['duration'] for item in details_response['items']}


    for video_id in video_ids:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        video_duration = durations.get(video_id, "Unknown duration")
        print(f"{video_url} | Duration: {video_duration[2:]}")
