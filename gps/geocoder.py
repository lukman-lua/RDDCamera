import requests
import re

url = "https://maps.app.goo.gl/B8uESB8wKUJfH6Gr9"

# expand short url
r = requests.get(url, allow_redirects=True)


headers = {
    "User-Agent": "Mozilla/5.0"
}

rs = requests.get(r.url, headers=headers, allow_redirects=True)

match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', rs.url)
print(rs.url)

if match:
    lat = match.group(1)
    lon = match.group(2)

    print(lat, lon)