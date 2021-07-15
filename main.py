import json
import os
from dataclasses import dataclass
from typing import List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

DISCORD_CHANNEL = os.getenv("DISCORD_CHANNEL")
DISCORD_KEY = os.getenv("DISCORD_KEY")
DISC_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "discs.json")
URLS_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "urls.json")


@dataclass
class DiscDelta:
    brand: str
    label: str
    title: str
    img: str
    price: float
    url: str

    def get_formatted_title(self):
        return "[{}] {}".format(self.brand, self.title)

    def get_discord_embed(self):
        return {"title": self.get_formatted_title(),
                "description": "${:.2f}".format(self.price),
                "url": self.url,
                "image": {"url": self.img}}


def post_to_discord(discs: List[DiscDelta]):
    url = "https://discord.com/api/v9/channels/{}/messages".format(DISCORD_CHANNEL)
    embeds = [disc.get_discord_embed() for disc in discs]
    payload = {"embeds": embeds}
    headers = {"Authorization": "Bot {}".format(DISCORD_KEY)}
    result = requests.post(url, json=payload, headers=headers)

    if result.status_code != 200:
        print(result.status_code, result.content)


def load_config(file_path: str):
    if not os.path.exists(file_path):
        return {}

    with open(file_path) as disc_file:
        discs = json.load(disc_file)
    return discs


def get_other_discs(url):
    results = {}

    page_data = requests.get(url).content
    soup = BeautifulSoup(page_data, "html.parser")
    products = soup.html.find_all("div", class_="l-products-item")
    parsed_url = urlparse(url)
    root = "{}://{}".format(parsed_url.scheme, parsed_url.hostname)

    for product in products:
        product_info = product.find(class_="product-info")
        title_tag = product_info.find(class_="product-title")
        in_stock = product_info.find(class_="product-id-stock").find(class_="lbl-stock").text
        disc_name = title_tag.span.text

        if not in_stock or "In stock" != in_stock:
            continue
        parsed_prod_url = urlparse(root + title_tag["href"])

        disc_url = root + parsed_prod_url.path
        disc_img = root + product.find(class_="product-img").find("img")["data-src"]
        disc_price_str = product_info.find("meta", itemprop="price")["content"]
        disc_price = float(disc_price_str.replace("$", ""))
        results[disc_name] = {"img": disc_img, "price": disc_price, "url": disc_url}

    return results


def get_pro_shop_discs(url):
    results = {}

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

    return results


def main():
    local_discs = load_config(DISC_FILE)

    urls = load_config(URLS_FILE)
    new_discs = {}
    updates: List[DiscDelta] = []

    for company, categories in urls.items():
        new_discs[company] = {}
        print("Fetching Discs for {}".format(company))
        for category, url in categories.items():
            print("\t-> {}".format(category))
            discs = get_pro_shop_discs(url) if "proshop" in url else get_other_discs(url)
            new_discs[company][category] = discs
            print("\t\t->Fetched {}".format(len(discs)))

            for disc_name, disc_info in discs.items():
                if (company in local_discs) and (category in local_discs[company]):
                    if disc_name not in local_discs[company][category]:
                        updates.append(DiscDelta(brand=company, label=category, title=disc_name, img=disc_info["img"],
                                                 price=disc_info["price"], url=disc_info["url"]))

    for update in updates:
        print(update.get_formatted_title())

    if local_discs and DISCORD_KEY and DISCORD_CHANNEL:
        post_to_discord(updates)

    with open(DISC_FILE, "w") as disc_file:
        json.dump(new_discs, disc_file, indent=2)


main()
