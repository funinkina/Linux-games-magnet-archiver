import aiohttp
import asyncio
import aiofiles
from bs4 import BeautifulSoup
import csv
from urllib.parse import urlparse

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


async def fetch_and_save_game_details(session, game_link, writer):
    async with session.get(game_link) as response:
        if response.status == 200:
            content = await response.text()
            soup = BeautifulSoup(content, "lxml")
            title = soup.find("h1", class_="title").text.strip()
            extra_info = ""
            file_size = ""
            magnet_link = ""

            for div in soup.find_all("div", class_="entry-content"):
                if div.find("blockquote"):
                    extra_info = div.find("blockquote").text.strip().replace("-", "")

                ems = div.find_all("em")
                for el in ems:
                    if el.text.startswith("File Size:"):
                        file_size = el.text.replace("File Size:", "").strip()
                magnet_links = div.find_all("a")
                for link in magnet_links:
                    href = link.get("href", "")
                    if href.startswith("magnet:?"):
                        magnet_link = href

            await writer.writerow([title, extra_info, file_size.strip(), magnet_link])
            print(f"Saved details for: {title}")
        else:
            print(f"Failed to retrieve {game_link}. Status code: {response.status}")


async def main():
    async with aiohttp.ClientSession(headers=headers) as session:
        async with aiofiles.open(
            "game_details.csv", mode="w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.writer(file)
            # Update CSV header to include File Size
            await writer.writerow(["Title", "Extra Info", "File Size", "Magnet Link"])

            async with session.get(
                "https://freelinuxpcgames.com/all-games/"
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, "lxml")
                    game_links = [
                        anchor.get("href")
                        for li in soup.find_all("div", class_="items-outer")
                        for anchor in li.find_all("a")
                    ]
                    valid_links = [link for link in game_links if is_valid_url(link)]
                    invalid_links = [
                        link for link in game_links if not is_valid_url(link)
                    ]

                    if invalid_links:
                        print(f"Found {len(invalid_links)} invalid URLs:")
                        for link in invalid_links:
                            print(f"Invalid URL: {link}")

                    print(f"Processing {len(valid_links)} valid URLs...")
                    tasks = [
                        fetch_and_save_game_details(session, link, writer)
                        for link in valid_links
                    ]
                    await asyncio.gather(*tasks)
                else:
                    print(
                        f"Failed to retrieve the main page. Status code: {response.status}"
                    )


if __name__ == "__main__":
    asyncio.run(main())
