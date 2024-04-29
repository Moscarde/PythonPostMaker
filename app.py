from modules.scraper.linkedin_scraper import LinkedinScraper
from modules.image_builder.image_builder import ImageBuilder
import os, webbrowser
import yaml


def cli():
    print("\n Carregar configurações customizadas?(config.yaml)")

    res = input("S/N: ")
    if res.lower() == "s":
        configs = read_config()
    else:
        configs = read_config(default=True)
        print("Carregando configurações padrão!")

    options = {
        1: lambda: build_controller(multiple=False, configs=configs),
        2: lambda: build_controller(multiple=True, configs=configs),
        3: exit,
        4: debug_builder,
    }

    print("\n-> Extração de dados do LinkedIn")
    print("Selecione uma opção:")
    print("[1] URL única")
    print("[2] URLs em lote")
    print("[3] Sair")

    while True:
        try:
            option = int(input("> "))
            if option in options:
                options[option]()
                break
            else:
                print("Opção inválida. Tente novamente.")
        except ValueError:
            print("Opção inválida. Tente novamente.")


def build_controller(multiple: bool, configs: dict):
    print()
    urls = request_multiple_urls() if multiple else request_single_url()

    scraped_data_paths = scrap_data(urls)

    for data_path in scraped_data_paths:
        build_images(data_path, configs=configs)
        open_output(data_path)


def request_multiple_urls() -> list:
    print("* Cole as URLs uma por vez ou separadas por espaçamento")
    print("* Para finalizar a lista, entre em uma linha em branco")

    urls = []

    while True:
        url = input("URL: ")

        if url == "":
            break

        if "linkedin" not in url:
            print("URL inválida. Tente novamente. (não contém 'linkedin')")
            continue

        urls.append(url.split(" "))
    
    urls = [item for sublist in urls for item in sublist]
    print("URLs coletadas:", len(urls))
    return urls


def request_single_url() -> list:
    print("* Cole a URL")

    while True:
        url = input("URL: ")
        if "linkedin" not in url:
            print("URL inválida. Tente novamente. (não contém 'linkedin')")
            continue
        else:
            return [url]


def scrap_data(urls: list):
    print("Coletando dados...")
    
    output_paths = []
    scraper = LinkedinScraper()
    for url in urls:
        scraper.scrape_data(url=url, debug=True)
        output_paths.append(scraper.output_path)
    scraper.close()

    return output_paths


def build_images(output_path, configs):
    print("Iniciando processamento de imagens")
    image_builder = ImageBuilder(path=output_path)

    print(" " * 6, "Autor:", image_builder.data["author"]["name"])
    print(
        " " * 6, "Texto:", image_builder.data["content"]["text"][:50].replace("\n", " ")
    )
    print(" " * 6, "Comentários:", len(image_builder.data["comments"]))
    print(" " * 6, "Imagens:", len(image_builder.data["content"]["img_filenames"]))

    image_builder.build(
        anonymous=configs["anom_users"],
        background_carrossel=configs["background_carrossel"],
        background=configs["background"],
    )


def open_output(output_path):
    print("Abrindo pasta de saida...\n")
    webbrowser.open(os.path.realpath(output_path))


def read_config(default=False):
    if default:
        path = "assets/default_config.yaml"
    else:
        path = "config.yaml"

    with open(path, "r") as file:
        return yaml.load(file, Loader=yaml.FullLoader)


def debug_builder():
    image_builder = ImageBuilder(path="last_scrap")
    image_builder.build(
        anonymous=True,
        background_carrossel=True,
        background="soujunior_1-8",
    )
    open_output(image_builder.path)


if __name__ == "__main__":
    # debug_builder() # exemplo de uso para testes
    cli()