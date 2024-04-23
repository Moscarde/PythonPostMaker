import json
from selenium import webdriver
import os

from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from bs4 import BeautifulSoup
from time import sleep
import json


def get_data(url):
    driver = webdriver.Chrome()
    driver.get(url)

    xpath_close_modal = (
        "//icon[contains(@class, 'contextual-sign-in-modal__modal-dismiss-icon')]"
    )
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath_close_modal))
        ).click()
        print("Fechando modal login")
    except:
        print("Extraindo dados")

    post = {}
    xpath_post_text = "//p[contains(@class, 'attributed-text-segment-list__content')]"
    post_text = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, xpath_post_text))
    )
    print(post_text.text)
    post["conteudo_texto"] = post_text.text

    xpath_autor_name = "//a[@data-tracking-control-name='public_post_feed-actor-name']"
    xpath_autor_subtitle = f"{xpath_autor_name}/../../p"
    xpath_autor_image = (
        "//a[@data-tracking-control-name='public_post_feed-actor-image']"
    )
    # original_poster = soup.find(attrs={"data-tracking-control-name": "public_post_feed-actor-name"})
    autor_name = driver.find_element(by=By.XPATH, value=xpath_autor_name).text
    autor_image_src = (
        driver.find_element(by=By.XPATH, value=xpath_autor_image)
        .find_element(by=By.TAG_NAME, value="img")
        .get_attribute("src")
    )
    autor_subtitle = driver.find_element(by=By.XPATH, value=xpath_autor_subtitle).text

    post["autor_name"] = autor_name
    post["autor_subtitle"] = autor_subtitle
    post["imagem_autor_src"] = autor_image_src
    print("Autor:", autor_name)
    print("Subtitle:", autor_subtitle)

    xpath_post_content_imges = "//ul[@data-test-id='feed-images-content']/li"

    li_images = driver.find_elements(by=By.XPATH, value=xpath_post_content_imges)
    conteudo_imagem = (
        li_images[0].find_element(by=By.TAG_NAME, value="img").get_attribute("src")
    )
    post["conteudo_imagem"] = conteudo_imagem

    # reactions
    xpath_reactions = (
        "//div[contains(@class, 'main-feed-activity-card__social-actions')]"
    )

    post["reacoes"] = driver.find_element(by=By.XPATH, value=xpath_reactions).text
    print(post["reacoes"])

    post["comentarios"] = []
    xpath_comentario = "//section[contains(@class, 'comment')]"
    comentarios = driver.find_elements(by=By.XPATH, value=xpath_comentario)

    driver.execute_script("arguments[0].scrollIntoView();", comentarios[0])
    sleep(1)

    for comentario in comentarios:
        comentario = BeautifulSoup(comentario.get_attribute("outerHTML"), "html.parser")
        comentario_header = comentario.find(class_="comment__header").text.split("\n")
        current_comment = {}
        current_comment["profile_url"] = comentario.find("div").find("a").get("href").split("?")[0]
        current_comment["profile_image_src"] = comentario.find("img").get("src")
        current_comment["autor"] = comentario_header[0]
        current_comment["sub"] = comentario_header[1]
        current_comment["tempo"] = comentario_header[2]
        current_comment["content_text"] = comentario.find(class_="comment__text").text
        post["comentarios"].append(current_comment)

    driver.find_element(by=By.TAG_NAME, value="img").screenshot(f"scraped/op_photo.png")

    with open("scraped/file.json", "w", encoding="utf-8") as file:
        json.dump(post, file, ensure_ascii=False)

    print("Scraping Finalizado")
