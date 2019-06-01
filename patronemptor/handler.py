import re

from botocore.vendored import requests


def url_parser(event, context):
    url = event

    r = requests.get(url)

    title = re.search(
        '(?<=<title>).+?(?=</title>)',
        r.text,
        re.DOTALL
    ).group().strip()

    return title
