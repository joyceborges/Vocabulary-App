from dotenv import load_dotenv
import itertools

import requests
import urllib.request
import string
import os
from datetime import date

from PIL import Image, ImageEnhance
import filetype
import pytesseract

from EnglishRequest import EnglishRequestMerriam

def input_image(input_path,
                sep=' '):
    img = Image.open(input_path)
    result = pytesseract.image_to_string(img, config=r'--oem 3 --psm 6')
    result = [item.split(sep) for item in result.splitlines()]
    return list(itertools.chain(*result))

if __name__ == "__main__":
    # TODO: CRIAR ARQUVIO PARA TESTAR
    # TODO: CONFIGURAR ENTRADAS - 1.LISTA DE PALAVRAS; 2. IMAGEM
    # TODO: CONFIGURAR AS EXCESSOES

    input_kind = 'IMAGE'
    if input_kind == 'IMAGE':
        input_path = "C:\\Users\\jlizc\\Documents\\PycharmProjects\\vocabularyapp\\print.jpg" # teste
        words = input_image(input_path)
    elif input_kind == 'TEXT':
        words = ['kamel']
    else:
        words = []

    load_dotenv()
    directory = "vocabularyapp"
    API_KEY_COLLEGIATE = os.getenv("API_KEY_COLLEGIATE")
    er = EnglishRequestMerriam(key=API_KEY_COLLEGIATE)
    er.create_folder()

    errors = []
    # process
    for word in words:
        try:
            print(word)
            w = er.request_word(word, download_audio=True,dictionary_type="collegiate")
            print(w)
        except requests.exceptions.JSONDecodeError as e:
            print(e)
        except Exception as e:
            print(e)
            print("An unexpected error occurred")

    print(f"We search for {len(words)}")
    print(f"We find {len(words)- len(errors)} words using this dictionary")
