import json
from selenium import webdriver
import os
import re
from bs4 import BeautifulSoup

# from selenium.webdriver.chrome.options import Options

# webdriver-manager
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager

# selenium tools
from selenium.webdriver.common.by import By

# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# from selenium.webdriver.remote.webdriver import WebElement
# from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from time import sleep
import json
from datetime import datetime

import shutil


def clear_text(text):
    # Remove caracteres não permitidos e converte para minúsculas
    text = re.sub(r"[^a-zA-Z0-9]", "_", text.lower())
    return text


class LinkedinScraper:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.base_path = "scraped/" + self.date
        self.output_path = ""  # utilizado para debug

    def scrape_data(self, url, debug):
        self.driver.get(url)
        self.close_sign_modal()

        if not self.verify_content():
            print("Conteúdo indisponível")
            return None

        data = self.get_data()
        if data:
            self.save_data(data)

        if debug:
            self.debug_data()

    def close_sign_modal(self):
        xpath_close_modal = (
            "//icon[contains(@class, 'contextual-sign-in-modal__modal-dismiss-icon')]"
        )
        try:
            WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, xpath_close_modal))
            ).click()
            return True
        except TimeoutException:
            return False

    def verify_content(self):
        # 1
        if not "linkedin.com" in self.driver.current_url:
            return False

        # 2
        try:
            self.driver.find_element(by=By.TAG_NAME, value="article")
        except NoSuchElementException:
            return False

        # 3
        try:
            xpath_content_unavailable = "//a[@data-tracking-control-name='public_post_content-unavailable-join']"
            WebDriverWait(self.driver, 1.5).until(
                EC.element_to_be_clickable((By.XPATH, xpath_content_unavailable))
            )
            return False
        except TimeoutException:
            return True

    def get_data(self):
        data = {}
        try:
            for i in range(9):
                self.driver.execute_script(f"window.scrollTo(0, {300 * i});")
                sleep(0.5)

            article_element = self.driver.find_element(by=By.TAG_NAME, value="article")
            soup_article = BeautifulSoup(
                article_element.get_attribute("outerHTML"), "html.parser"
            )

            data["autor"] = self.get_autor(soup_article)

            data["content"] = self.get_content(soup_article)

            data["comments"] = self.get_comments(soup_article)

            return data
        except Exception as e:
            print(e)
            return None

    def get_autor(self, soup_article):
        header = soup_article.find(
            "div", attrs={"data-test-id": "main-feed-activity-card__entity-lockup"}
        )
        header_content = [
            item.strip() for item in header.text.split("\n") if item.strip()
        ]

        name = header.find(
            attrs={"data-tracking-control-name": "public_post_feed-actor-name"}
        ).text.strip()
        headline = header_content[1]
        post_age = header_content[2]

        img_src = header.find("img").get("src")

        return {
            "name": name,
            "headline": headline,
            "post_age": post_age,
            "img_src": img_src,
        }

    def get_content(self, soup_article):
        content_text = soup_article.find(
            "p", class_="attributed-text-segment-list__content"
        ).text

        content_type = "text"
        content_imgs_src = []

        try:
            content_imgs = soup_article.find(
                attrs={"data-test-id": "feed-images-content"}
            )
            if content_imgs:
                content_imgs = content_imgs.find_all("img")
                content_imgs_src = [img.get("src") for img in content_imgs]
                content_type = "image"

            content_video = soup_article.find_all("video")
            if content_video:
                content_imgs_src = [
                    video.get("data-poster-url") for video in content_video
                ]
                content_type = "video"

        except NoSuchElementException:
            print("Tipo de postagem não suportado. Falha ao capturar conteúdo")

        reactions_element = soup_article.find(
            "div", class_="main-feed-activity-card__social-actions"
        ).text

        reactions = [
            item.strip() for item in reactions_element.split("\n") if item.strip()
        ]

        return {
            "text": content_text,
            "imgs_src": content_imgs_src,
            "type": content_type,
            "reactions": reactions,
        }

    def get_comments(self, soup_article):
        comments_element = soup_article.find_all("section", class_="comment")[:2]

        comments = []
        for index, comment in enumerate(comments_element):
            current_comment = {}

            comment_header = comment.find(class_="comment__header").text.split("\n")
            comment_header_texts = [
                item.strip() for item in comment_header if item.strip()
            ]

            autor = comment_header_texts[0]
            headline = comment_header_texts[1]
            comment_age = comment_header_texts[2]

            profile_url = comment.find("a").get("href").split("?")[0]
            profile_image_src = comment.find("img").get("src")
            comment_text = comment.find(class_="comment__text").text

            image_index = str(index)
            comments.append(
                {
                    "autor": autor,
                    "headline": headline,
                    "comment_age": comment_age,
                    "profile_url": profile_url,
                    "profile_image_src": profile_image_src,
                    "comment_text": comment_text,
                }
            )

        return comments

    def save_data(self, data):
        folder_name_autor = clear_text(data["autor"]["name"])
        folder_name_post = clear_text(data["content"]["text"][:20])

        self.output_path = os.path.join(self.base_path, folder_name_autor, folder_name_post)

        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        with open(
            os.path.join(self.output_path, "data.json"), "w", encoding="utf-8"
        ) as outfile:
            json.dump(data, outfile, ensure_ascii=False)

        self.save_images(data)

    def save_images(self, data):
        self.driver.get(data["autor"]["img_src"])
        sleep(0.5)

        self.driver.find_element(by=By.TAG_NAME, value="img").screenshot(
            f"{self.output_path}/autor_img.png"
        )

        for index, img in enumerate(data["content"]["imgs_src"]):
            sleep(0.5)
            self.driver.get(img)
            self.driver.find_element(by=By.TAG_NAME, value="img").screenshot(
                f"{self.output_path}/content_img_{index}.png"
            )

        if data["comments"]:
            for index, comment in enumerate(data["comments"]):
                if "aero-" in comment["profile_image_src"]:
                    continue

                self.driver.get(comment["profile_image_src"])
                sleep(0.5)

                image_output_path = f"{self.output_path}/comment_profile_photo_{index}.png"

                self.driver.find_element(by=By.TAG_NAME, value="img").screenshot(
                    image_output_path
                )

    def debug_data(self):
        print("Saving data to debugging folder...")

        # copy to folder
        input_folder = self.output_path
        output_folder = "last_scrap"

        # delete old folder
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder, ignore_errors=True)

        shutil.copytree(input_folder, output_folder)

    def close(self):
        self.driver.close()


if __name__ == "__main__":
    # abrahan
    url = """https://www.linkedin.com/feed/update/urn:li:activity:7186083318310834177?updateEntityUrn=urn%3Ali%3Afs_feedUpdate%3A%28V2%2Curn%3Ali%3Aactivity%3A7186083318310834177%29
"""
    scraper = LinkedinScraper()
    scraper.scrape_data(url, debug=True)
    scraper.close()
