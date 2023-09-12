import requests, os, json
from dotenv import load_dotenv


load_dotenv()

yt_key = os.environ.get("YT_KEY")
youtube_url_base = "https://www.googleapis.com/youtube/v3"


def search(q: str):
    """
    q: {
        type: str,
        description: This stands for search string
    }
    """

    url = f"{youtube_url_base}/search?type=video&q={q}"
    params = {"key": yt_key}

    response = requests.get(url=url, params=params)

    print(response.status_code)

    if response.status_code == 200 and response.content:
        return json.loads(response.content)
    else:
        return {"status_code": response.status_code}


def video_by_id(id: str):
    url = f"{youtube_url_base}/videos?part=id%2Csnippet&id={id}"
    params = {"key": yt_key}

    response = requests.get(url=url, params=params)

    print(response.status_code)
    if response.status_code == 200:
        return json.loads(response.content)
    else:
        return {}
