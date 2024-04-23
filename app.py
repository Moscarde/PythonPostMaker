from test_scrap import get_data
from test_builder import image_builder

if __name__ == "__main__":
    post_url = "https://www.linkedin.com/posts/thiagolisboapro_siga-sua-paix%C3%A3o-%C3%A9-um-dos-piores-conselhos-activity-7185286041614905344-smY7?utm_source=share&utm_medium=member_desktop"
    get_data(post_url)
    image_builder("scraped/file.json")

