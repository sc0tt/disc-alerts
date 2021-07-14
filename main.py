from dataclasses import dataclass
import json
import os


from bs4 import BeautifulSoup
import requests

DISCORD_CHANNEL = os.getenv("DISCORD_CHANNEL")
DISCORD_KEY = os.getenv("DISCORD_KEY")
DISC_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "discs.json")

@dataclass
class Disc:
  title: str
  url: str
  img: str
  price: float

def post_to_discord(discs):
  url = "https://discord.com/api/v9/channels/{}/messages".format(DISCORD_CHANNEL)
  embeds = []
  for disc in discs:
    embeds.append({"title": disc.title, "description": "${:.2f}".format(disc.price), "url": disc.url, "image": {"url": disc.img}})
  payload = {"content": "NEW DISCS IN STOCK", "embeds": embeds}
  headers = {"Authorization": "Bot {}".format(DISCORD_KEY)}
  result = requests.post(url, json=payload, headers=headers)
  if result.status_code != 200:
    print(result.status_code, result.content)

def load_discs():
  if not os.path.exists(DISC_FILE):
    return {}
  
  with open(DISC_FILE) as disc_file:
    discs = json.load(disc_file)
  return discs

def get_innova_discs(product_type):
  results = {}
  url = "https://proshop.innovadiscs.com/{}/?limit=96".format(product_type)
  page_data = requests.get(url).content
  soup = BeautifulSoup(page_data, "html.parser")

  products = soup.html.find_all("li", class_="product")
  for product in products:
    title_tag = product.find("h3", class_="card-title")
    disc_name = title_tag.a.text
    disc_url = title_tag.a["href"]
    disc_img = product.find("img")["src"]
    disc_price_str = product.find(class_="price--withoutTax").text
    disc_price = float(disc_price_str.replace("$", ""))
    results[disc_name] = {"img": disc_img, "price": disc_price, "url": disc_url}
  
  return {product_type: results}

def find_new_discs(old, new):
  new_discs = []
  for disc_name, disc_info in new.items():
    if disc_name not in old:
       new_discs.append(Disc(title=disc_name, url=disc_info["url"], img=disc_info["img"], price=disc_info["price"]))
  return new_discs

def main():
  local_discs = load_discs()

  limited_innova_discs = get_innova_discs("limited")
  normal_innova_discs = get_innova_discs("full-production")
  current_discs = {"innova": {**limited_innova_discs, **normal_innova_discs}}
    
  if local_discs:
    new_limited_discs = find_new_discs(local_discs["innova"]["limited"], current_discs["innova"]["limited"])
    if new_limited_discs:
      post_to_discord(new_limited_discs)

  with open(DISC_FILE, "w") as disc_file:
    json.dump(current_discs, disc_file, indent=2)


main()
