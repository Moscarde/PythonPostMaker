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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
from time import sleep
import json
from datetime import datetime

import shutil


def clear_text(text) -> str:
    """
    Substitui caracteres não alfanuméricos em uma string por underscores e converte
    a string para minúsculas.

    Parâmetros:
        text (str): A string que será limpa.

    Retorna:
        str: A string limpa, com caracteres não alfanuméricos substituídos por underscores
        e convertida para minúsculas.
    """
    text = re.sub(r"[^a-zA-Z0-9]", "_", text.lower())
    return text


class LinkedinScraper:
    """
    Classe para realizar scraping de dados do LinkedIn.

    Atributos:
        driver (WebDriver): O driver do navegador.
        date (str): A data atual no formato 'YYYY-MM-DD'.
        base_path (str): O caminho base para salvar os dados raspados.
        output_path (str): O caminho de saída para os dados raspados.

    Métodos:
        __init__(): Inicializa a instância da classe e configura os atributos necessários.
        scrape_data(url, debug=False): Realiza o scraping de dados de uma URL do LinkedIn.
    """

    def __init__(self):
        """
        Inicializa a instância da classe e configura os atributos necessários.
        """
        self.driver = webdriver.Chrome()
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.base_path = "scraped/" + self.date
        self.output_path = ""  

    def scrape_data(self, url, debug = False):
        """
        Realiza o scraping de dados de uma URL do LinkedIn.

        Parâmetros:
            url (str): A URL da postagem no LinkedIn.
            debug (bool, optional): Se True, salva informações coletadas também na pasta last_scraped. Default False.

        Retorna:
            None: Se não foi possível obter os dados.
        """
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
        """
        Fecha o modal de login, se estiver presente.

        Retorna:
            bool: True se o modal foi fechado com sucesso, False se não foi possível fechar o modal dentro do tempo limite.
        """
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
        """
        Verifica se o conteúdo na página do LinkedIn está disponível.

        Retorna:
            bool: True se o conteúdo estiver disponível, False se não estiver disponível.
        """
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
        """
        Obtém os dados da página.

        Retorna:
            dict: Um dicionário contendo os dados obtidos da página.
                As chaves incluem 'author', 'content' e 'comments'.
                Cada chave está associada aos dados relevantes obtidos da página.
                Se ocorrer um erro durante a obtenção dos dados, retorna None.
        """
        data = {}
        try:
            for i in range(9):
                self.driver.execute_script(f"window.scrollTo(0, {300 * i});")
                sleep(0.5)

            article_element = self.driver.find_element(by=By.TAG_NAME, value="article")
            soup_article = BeautifulSoup(
                article_element.get_attribute("outerHTML"), "html.parser"
            )

            data["author"] = self.get_author(soup_article)

            data["content"] = self.get_content(soup_article)

            data["comments"] = self.get_comments(soup_article)

            return data
        except Exception as e:
            print(e)
            return None

    def get_author(self, soup_article):
        """
        Obtém informações do autor do artigo.

        Parâmetros:
            soup_article (BeautifulSoup): Um objeto BeautifulSoup representando o artigo.

        Retorna:
            dict: Um dicionário contendo informações do autor, incluindo nome, headline,
            idade do post, URL da imagem e nome do arquivo de imagem.
        """
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
            "img_filename": "author_img.png",
        }

    def get_content(self, soup_article):
        """
        Obtém o conteúdo do artigo.

        Parâmetros:
            soup_article (BeautifulSoup): Um objeto BeautifulSoup representando o artigo.

        Retorna:
            dict: Um dicionário contendo o texto do conteúdo, URLs das imagens, tipo de conteúdo,
                reações e nomes de arquivo das imagens.
        """
        content_text = soup_article.find(
            "p", class_="attributed-text-segment-list__content"
        ).text

        content_type = "text"

        media = self.get_media(soup_article)
        if media is not None:
            content_imgs_src, content_type = media
        else:
            content_imgs_src = []

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
            "img_filenames": [f"content_img_{index}.png" for index in range(len(content_imgs_src))],
        }

    def get_media(self, soup_article):
        """
        Obtém mídia do artigo.

        Parâmetros:
            soup_article (BeautifulSoup): Um objeto BeautifulSoup representando o artigo.

        Retorna:
            tuple or None: Uma tupla contendo as URLs da mídia e o tipo de mídia, se encontradas,
            caso contrário, retorna None.
        """
        media_photo_video = self.get_media_photo_video(soup_article)
        if media_photo_video is not None:
            return media_photo_video

        media_iframe =  self.get_media_iframe()
        if media_iframe is not None:
            return media_iframe
        
        return None

    def get_media_photo_video(self, soup_article):
        """
        Obtém fotos ou vídeos do artigo.

        Parâmetros:
            soup_article (BeautifulSoup): Um objeto BeautifulSoup representando o artigo.

        Retorna:
            tuple or None: Uma tupla contendo as URLs da mídia e o tipo de mídia, se encontradas,
            caso contrário, retorna None.
        """
        try:
            content_imgs_src = []
            
            content_imgs = soup_article.find(
                attrs={"data-test-id": "feed-images-content"}
            )
            if content_imgs:
                content_imgs = content_imgs.find_all("img")
                content_imgs_src = [img.get("src") for img in content_imgs]
                content_type = "image"
                return content_imgs_src, content_type   

            content_video = soup_article.find_all("video")
            if content_video:
                content_imgs_src = [
                    video.get("data-poster-url") for video in content_video
                ]
                content_type = "video"

                return content_imgs_src, content_type
            
            return None

        except NoSuchElementException:
            print("Tipo de postagem não suportado. Falha ao capturar conteúdo de mídia")
            return None
        except Exception as e:
            print(e)
            return None
    
    def get_media_iframe(self):
        """
        Obtém mídia do tipo iframe.

        Retorna:
            tuple or None: Uma tupla contendo as URLs da mídia e o tipo de mídia, se encontradas,
            caso contrário, retorna None.
        """
        try:
            xpath_iframe = "//iframe[@data-id='feed-paginated-document-content']"
            iframe = self.driver.find_element(by=By.XPATH, value=xpath_iframe)
            self.driver.switch_to.frame(iframe)
            iframe_html = self.driver.page_source

            button_next = self.driver.find_elements(
                by=By.CLASS_NAME, value="ssplayer-carousel-panel"
            )[-1]

            count=0
            while True:
                try:
                    button_next.click()
                    sleep(0.5)
                    count+=1

                    if count == 12:
                        break
                except ElementNotInteractableException:
                    break

            iframe_html = self.driver.page_source
            soup_iframe = BeautifulSoup(iframe_html, "html.parser")
            content_img_ul = soup_iframe.find("div", class_="carousel-track-container")
            content_carrossel_imgs = content_img_ul.find_all("img")
            content_imgs_src = [img.get("src") for img in content_carrossel_imgs]
            content_type = "image"

            print("...iframe media loaded")
            print(content_imgs_src)

            return content_imgs_src, content_type
        
        except Exception as e:
            print(e)
            print("...iframe media not loaded")
            return None



    def get_comments(self, soup_article):
        """
        Obtém os comentários do artigo.

        Parâmetros:
            soup_article (BeautifulSoup): Um objeto BeautifulSoup representando o artigo.

        Retorna:
            list: Uma lista de dicionários, cada um representando um comentário. Cada dicionário
                contém informações sobre o autor do comentário, incluindo nome, headline, idade do comentário,
                URL do perfil, URL da imagem de perfil, texto do comentário e nome do arquivo da imagem de perfil.
                Retorna uma lista vazia se não houver comentários.
        """
        comments_element = soup_article.find_all("section", class_="comment")[:3]

        comments = []
        for index, comment in enumerate(comments_element):

            comment_header = comment.find(class_="comment__header").text.split("\n")
            comment_header_texts = [
                item.strip() for item in comment_header if item.strip()
            ]

            author = comment_header_texts[0]
            headline = comment_header_texts[1]
            comment_age = comment_header_texts[2]

            profile_url = comment.find("a").get("href").split("?")[0]
            profile_image_src = comment.find("img").get("src")
            comment_text = comment.find(class_="comment__text").text

            comments.append(
                {
                    "author": author,
                    "headline": headline,
                    "comment_age": comment_age,
                    "profile_url": profile_url,
                    "profile_image_src": profile_image_src,
                    "comment_text": comment_text,
                    "img_filename": f"comment_profile_photo_{index}.png",
                }
            )

        return comments

    def save_data(self, data):
        """
        Salva os dados coletados em um arquivo JSON e as imagens em uma pasta.

        Parâmetros:
            data (dict): Um dicionário contendo os dados a serem salvos.

        Retorna:
            None
        """
        folder_name_author = clear_text(data["author"]["name"])
        folder_name_post = clear_text(data["content"]["text"][:20])

        self.output_path = os.path.join(
            self.base_path, folder_name_author, folder_name_post
        )

        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        with open(
            os.path.join(self.output_path, "data.json"), "w", encoding="utf-8"
        ) as outfile:
            json.dump(data, outfile, ensure_ascii=False)

        self.save_images(data)

    def save_images(self, data):
        """
        Salva as imagens relacionadas aos dados coletados em uma pasta.

        Parâmetros:
            data (dict): Um dicionário contendo os dados que incluem informações sobre as imagens.

        Retorna:
            None
        """
        self.driver.get(data["author"]["img_src"])
        sleep(0.5)

        self.driver.find_element(by=By.TAG_NAME, value="img").screenshot(
            f"{self.output_path}/{data['author']['img_filename']}"
        )

        for index, img in enumerate(data["content"]["imgs_src"]):
            if "https://" not in img:
                continue
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

                image_output_path = f"{self.output_path}/{comment['img_filename']}"

                self.driver.find_element(by=By.TAG_NAME, value="img").screenshot(
                    image_output_path
                )

    def debug_data(self):
        """
        Salva os dados coletados em uma pasta de depuração para análise.

        Retorna:
            None
        """
        print("Saving data to debugging folder...")

        # copy to folder
        input_folder = self.output_path
        output_folder = "last_scrap"

        # delete old folder
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder, ignore_errors=True)

        shutil.copytree(input_folder, output_folder)

    def close(self):
        """
        Fecha o navegador após a conclusão da tarefa.

        Retorna:
            None
        """
        self.driver.close()


if __name__ == "__main__":
    url = """https://www.linkedin.com/posts/enriquemross_prot%C3%B3tipos-dos-dashboards-ugcPost-7187964353617285120-ul4Q?utm_source=share&utm_medium=member_desktop
"""
    scraper = LinkedinScraper()
    scraper.scrape_data(url, debug=True)
    scraper.close()
    print("Done")
