import json
import os
from datetime import datetime, date
import asyncio
import re
import requests
import pandas as pd
from telegram import Bot
from decouple import config
from loguru import logger

SENT_FILE = "sent_ads.json"
LOG_FILE = "ads_log.log"

logger.add(LOG_FILE, rotation="1 MB", retention="7 days", level="INFO", encoding="utf-8")


def load_sent_ads():
    if not os.path.exists(SENT_FILE):
        return {"date": str(date.today()), "urls": []}

    with open(SENT_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {"date": str(date.today()), "urls": []}

    if data.get("date") != str(date.today()):
        return {"date": str(date.today()), "urls": []}

    return data


def save_sent_ads(data):
    with open(SENT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def buscar_motos_hoje(query: str):
    url = f"https://www.olx.com.br/autos-e-pecas/motos/estado-sp?q={query.replace(' ', '%20')}"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/115.0 Safari/537.36"}
    r = requests.get(url, headers=headers)

    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text, re.S)
    if not match:
        return pd.DataFrame()

    try:
        ads = json.loads(match.group(1))["props"]["pageProps"]["ads"]
    except Exception:
        return pd.DataFrame()

    hoje = date.today()
    resultados = []

    for ad in ads:
        titulo = ad.get("title") or ad.get("subject")
        preco = ad.get("price") or ad.get("priceValue")
        link = ad.get("url") or ad.get("friendlyUrl")
        timestamp = ad.get("created") or ad.get("date") or ad.get("origListTime") or ad.get("createdAt")

        if not timestamp or not link:
            continue

        try:
            dt = datetime.fromtimestamp(int(timestamp))
        except Exception:
            continue
        if dt.date() != hoje:
            continue

        resultados.append({
            "title": titulo,
            "price": preco,
            "url": link,
            "publication_date": dt.strftime("%d/%m/%Y %H:%M"),
        })

    return pd.DataFrame(resultados)


def to_ad_template(title: str, price: str, url: str, publication_date: str):
    return (
        f"📦 *{title}*\n"
        f"💰 Preço: {price}\n"
        f"📅 Publicado em: {publication_date}\n\n"
        f"🔗 [Ver anúncio]({url})"
    )


async def send_ads(ads):
    bot = Bot(config("TOKEN"))
    chat_id = config("CHAT_ID")

    for ad in ads:
        msg = to_ad_template(**ad)
        await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        logger.info(f"Anúncio enviado: {ad['title']} - {ad['url']}")
        await asyncio.sleep(1)


def run():
    sent_data = load_sent_ads()
    sent_urls = set(sent_data["urls"])
    products = ["Start 160", "Titan", "Honda CG 160"]
    novos_envios = []

    for product in products:
        ads = buscar_motos_hoje(product).to_dict(orient="records")

        for ad in ads:
            if ad["url"] not in sent_urls:
                novos_envios.append(ad)
                sent_urls.add(ad["url"])

    if novos_envios:
        asyncio.run(send_ads(novos_envios))
        sent_data["urls"] = list(sent_urls)
        save_sent_ads(sent_data)
        logger.info(f"{len(novos_envios)} novos anúncios enviados!")
    else:
        logger.info("Nenhum novo anúncio encontrado.")


if __name__ == "__main__":
    run()