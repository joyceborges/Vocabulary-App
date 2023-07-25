import requests
import urllib.request

from bs4 import BeautifulSoup
import string
from datetime import date

from dotenv import load_dotenv
import os


class Word:
    '''
    TODO: colocar um validador onde o primeiro item de meaning deve ser das palavras reservadas verbo, preposição
    '''
    def __init__(self, word, meanings=None, synonym=None, others=None):
        if others is None:
            others = []
        if synonym is None:
            synonym = []
        if meanings is None:
            meanings = []
        self._word = word
        self._meanings = {f"{word}:{item + 1}": meaning for item, meaning in enumerate(meanings)}
        self._synonym = synonym
        self._others = others

    def get_word(self):
        return self._word

    def get_meanings(self):
        return self._meanings

    def get_synonym(self):
        return self._synonym

    def get_others(self):
        return self._others

    def add_meaning(self, meanings):
        for meaning in meanings:
            self._meanings[f"{self._word}:{len(self._meanings) + 1}"] = meaning

    def add_others(self, words):
        if type(words) == str:
            words = [words]
        for word in words:
            self._others.append(word)

    def __print__(self):
        return f"Word {self._word}"

    def __repr__(self):
        result = f""" Word: {self._word}
           {self.get_meanings()}           
        """
        return result


class EnglishRequest:
    def __init__(self, key, filename='', path='.'):
        self._key = key
        if filename == '':
            self._filename = f"My Words in {date.today()}"
        else:
            self._filename = filename
        self._path = path

    def request_word(self, word_searched, download_audio=False, dictionary_type=""):
        pass

    def create_folder(self):

        try:
            path = os.path.join(self._path, self._filename)
            counter = 1
            while os.path.exists(path):
                path = os.path.join(self._path, f"{self._filename} ({str(counter)})")
                counter += 1
            self._path, self._filename = os.path.split(path)
            os.makedirs(path)
            return path
        except FileNotFoundError as e:
            print('FileNotFoundError: Please, check the path.')
        except FileExistsError as e:
            print('FileExistsError: There is a vocabulary folder')


class EnglishRequestOxford(EnglishRequest):

    def __init__(self, key, path='.'):
        super().__init__(key, path='.')

    def request_word(self, word_searched, download_audio=False, dictionary_type="Oxford Dict"):
        word = Word(word_searched)
        headers = {'User-Agent': 'Mozilla/5.0 Chrome/39.0.2171.95 Safari/537.36'}
        for n in range(1, 5):
            url = f"https://www.oxfordlearnersdictionaries.com/us/definition/english/{word_searched}_{n}"
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            word_returned = soup.find(hclass="headword")
            if word_returned:
                word_class = word_returned.find_next_sibling("span").text
                word_returned = word_returned.text
                if word_searched == word_returned:
                    defs = soup.find('ol', {"htag": "ol"}).find_all("span", {"hclass": "def"})
                    for definition in defs:
                        word.add_meaning([[word_class, definition.text]])

                    others = [word_other.text for word_other in soup.find('div', {"class": "idioms"}).find_all('span', {"class": "idm"})]
                    word.add_others(others)

                    # TODO AVOID THAT SAME AUDIO APPER SEVERA TIMES
                    if download_audio:  # TODO REFACTOR; download_audio must be a new function

                        # TODO protect when there are no sounds
                        sound_element = soup.find("div", {"class": "phons_br"}).find("div", {"class": "sound"})
                        value_ipa = sound_element.find_next_sibling("span").text.replace("/","")
                        path_download = os.path.join(self._path, self._filename,
                                                     f"{word_searched} "
                                                     f"[{value_ipa}] from {dictionary_type}.mp3")

                        with open(f'{path_download} - UK Oxford Dictionary.mp3', 'wb') as f:
                            f.write(requests.get(sound_element.get('data-src-mp3'), headers=headers).content)

                        sound_element = soup.find("div", {"class": "phons_n_am"}).find("div", {"class": "sound"})
                        value_ipa = sound_element.find_next_sibling("span").text.replace("/","")
                        path_download = os.path.join(self._path, self._filename,
                                                     f"{word_searched} "
                                                     f"[{value_ipa}]from {dictionary_type}.mp3")

                        with open(f'{path_download} - AM Oxford Dictionary.mp3', 'wb') as f:
                            f.write(requests.get(sound_element.get('data-src-mp3'), headers=headers).content)
            else:
                break

        return word


class EnglishRequestMerriam(EnglishRequest):

    def __init__(self, key, path='.'):
        super().__init__(key, path='.')

    def request_word(self, word_searched, download_audio=False, dictionary_type=""):
        if dictionary_type == '':
            dictionary_type = 'learners'  # 'collegiate'; TODO validate dict type previously

        d_requests = {'learners': "self._request_learner",
                      'collegiate': "self._request_collegiate"}

        word = None
        url = f'https://dictionaryapi.com/api/v3/references/' \
              f'{dictionary_type}/json/{word_searched}?key={self._key}'

        response = requests.get(url)

        if response.status_code == 200:
            word = Word(word_searched)
            response_json = response.json()

            if len(response_json) == 0:
                print(f'I can not found the word "{word_searched}"')
                return None
            elif type(response_json[0]) == str:
                print(f'I can not found the word "{word_searched}". Do you mean "{response_json[0]}"?')
                return None

            for meaning in response_json:
                word_returned = meaning.get('meta').get('id').split(':')
                if word_searched.upper() == word_returned[0].upper():
                    word_class, definitions = eval(d_requests.get(dictionary_type))(meaning)
                    word.add_meaning([[word_class, definitions]])
                    if download_audio and meaning.get('hwi').get('prs'):
                        self._download_audio(word_searched, dictionary_type, meaning)
                else:
                    word.add_others(word_returned)
        return word

    def _request_learner(self, meaning):
        word_class, definitions = None, None
        shortdef = meaning.get('meta').get('app-shortdef')  # ['meta']['app-shortdef']
        if shortdef:
            word_class = shortdef.get('fl')  # functional label ['fl']
            definitions = shortdef.get('def')  # ['def']
        return word_class, definitions

    def _request_collegiate(self,meaning):
        definitions = meaning.get('shortdef')
        word_class = meaning.get('fl')
        return word_class, definitions

    def _download_audio(self, word_searched, dictionary_type, meaning):
        root_audio = "https://media.merriam-webster.com/audio/prons/"
        language_code = 'en'
        country_code = 'us'
        format_audio = 'mp3'  # [wav, ogg]

        if dictionary_type == 'learners':
            value_ipa = meaning.get('hwi').get('prs')[0].get('ipa')
        else:
            value_ipa = meaning.get('hwi').get('prs')[0].get('mw')  # ['mw']

        base_filename = meaning.get('hwi').get('prs')[0].get('sound').get('audio')
        if word_searched[:3] == 'bix':
            subdirectory = 'bix'
        elif word_searched[:3] == 'gg':
            subdirectory = 'gg'
        elif word_searched[0].isnumeric() or word_searched[0] in string.punctuation:
            subdirectory = 'number'
        else:
            subdirectory = base_filename[0]

        audio_url = f"{root_audio}{language_code}/{country_code}/{format_audio}/{subdirectory}/{base_filename}.{format_audio}"
        path_download = os.path.join(self._path, self._filename,
                                    f"{word_searched} {meaning.get('meta').get('id').split(':')} - "
                                    f"{value_ipa} from {dictionary_type}.mp3")
        urllib.request.urlretrieve(audio_url, path_download)


if __name__ == "__main__":
    word = 'bear'
    er = EnglishRequestOxford(key=None)
    er.create_folder()
    w = er.request_word(word, download_audio=True)

    print(w)
    print(w.get_meanings())
    print(w.get_word())
    print(w.get_others())

    # load_dotenv()
    # API_KEY_LEARNERS = os.getenv("API_KEY_LEARNERS")
    # API_KEY_COLLEGIATE = os.getenv("API_KEY_COLLEGIATE")
    #
    # er = EnglishRequestMerriam(key=API_KEY_LEARNERS)
    # er.create_folder()
    #
    # word = 'agree'
    # word_1 = er.request_word(word, download_audio=True, dictionary_type="learners")
    # print("Learners: ", word_1.get_meanings())
    #
    # er._key = API_KEY_COLLEGIATE  # TODO add set to key
    # word_2 = er.request_word(word, download_audio=True, dictionary_type="collegiate")
    # print("Collegiate: ", word_2.get_meanings())
