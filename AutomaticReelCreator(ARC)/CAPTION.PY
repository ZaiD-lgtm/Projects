
def generate_caption(link,prompt):
    client = genai.Client(api_key=API_KEY)

    response = client.models.generate_content(
    model="gemini-2.5-pro", contents=types.Content(
        parts=[
            types.Part(
                file_data=types.FileData(file_uri=link)
            ),
            types.Part(text=prompt)
        ]
))
    text_return = response.text
    #print("RESPONSE:    ",text_return)
    captions_list =""
    flag = False
    for i in range(len(text_return)):
        if text_return[i] == "[" or  flag == True :
            flag = True
            if (text_return[i] == "'" and text_return[i -1]=='[') or (text_return[i] == "'" and text_return[i+1]==']'):
                captions_list +='"'
                continue
            captions_list +=text_return[i]
        if text_return[i] == ']':
            break
    captions_list = captions_list.strip().lstrip('\ufeff')
    return captions_list
    


link = "https://www.youtube.com/watch?v=OW1VPGmSIdk"
prompt_cap = f'''Give me the single best caption for this video inside a python list of string. eg: ["caption"]'''
caption_list = generate_caption(link,prompt_cap)
caption_list = json.loads(caption_list)