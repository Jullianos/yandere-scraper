from bs4 import BeautifulSoup
from datetime import datetime
from collections import defaultdict
import requests
import time
import json
import os
import re
import shutil


YANDERE_URL = 'https://yande.re/post/show/'
YANDERE_DOWNLOAD_LOCATION = 'images/yandere/'
MAIN_YANDERE_JSON_FILEPATH = 'json/yandere/yandere.json'


def download_image(url, name):
    while True:
        try:
            try:
                r = requests.get(url, allow_redirects=True)
                open(name, 'wb').write(r.content)
                break
            except ConnectionAbortedError:
                print('<-Connection Error (Image)-> reconnecting...')
                time.sleep(5)
        except requests.ConnectionError:
            print('<-Connection Error (Image)-> reconnecting...')
            time.sleep(5)


def get_last_index_from_yandere_json(filepath):

    # get the last index
    if os.path.isfile(MAIN_YANDERE_JSON_FILEPATH):
        with open(filepath, 'r') as main_file:
            try:
                data = json.loads(main_file.read())
            except json.decoder.JSONDecodeError:
                print('Main json file has invalid format.')
                return None

            last = 0
            for key, value in data.items():
                if int(key) > last:
                    last = int(key)
        return last

    print('No main json file.')

    return None


def scrape_images_from_yandere(Type):

    if Type == 'Continue':
        # get the last index
        # continue to scrape from the last index
        if os.path.isfile(MAIN_YANDERE_JSON_FILEPATH):
            x = get_last_index_from_yandere_json(MAIN_YANDERE_JSON_FILEPATH) + 1
        else:
            print('\nCannot Continue, there is no main json file.\n')
            return None

    elif Type == 'Initial':

        # if there is already a main file copy it and rename it, and remove the main file
        if os.path.isfile(MAIN_YANDERE_JSON_FILEPATH):
            shutil.copyfile(MAIN_YANDERE_JSON_FILEPATH, MAIN_YANDERE_JSON_FILEPATH +
                            str(datetime.now().strftime("%Y-%m-%d_%H-%M-%S")) + '.json')

            os.remove(MAIN_YANDERE_JSON_FILEPATH)

            with open(MAIN_YANDERE_JSON_FILEPATH, 'w') as new_file:
                new_file.write('{}')

                print('Main file for initial scrape created: "yandere.json"')
        else:
            with open(MAIN_YANDERE_JSON_FILEPATH, 'w') as new_file:
                new_file.write('{}')

                print('Main file for initial scrape created: "yandere.json"')

        x = 0

    else:
        return None

    if os.path.isfile(MAIN_YANDERE_JSON_FILEPATH):
        while True:
            while True:
                try:
                    try:
                        page = requests.get(YANDERE_URL + str(x), headers={'User-agent': 'Mr.163211'})
                        break
                    except ConnectionAbortedError:
                        print('<-Connection Error (Image)-> reconnecting...')
                        time.sleep(5)
                except requests.ConnectionError:
                    print('<-Connection Error-> reconnecting...')
                    time.sleep(5)

            if page.status_code == 404:
                print(str(x) + ' doesnt exist.')
                x += 1

            elif page.status_code == 200:
                deleted = False
                soup = BeautifulSoup(page.content, 'html.parser')

                # Check if the post was deleted
                notice = soup.find_all('div', attrs={'class': 'status-notice'})
                for div in notice:
                    if 'This post was deleted' in div.text:
                        deleted = True
                        break

                # If it was deleted skip this index
                if deleted:
                    print(str(x) + ' was deleted.')
                    x += 1
                    continue

                stats = {}

                # Get the image url and download it in the highest resolution
                try:
                    image_url_jpg = soup.find('a', id='highres')['href']

                    image_name = YANDERE_DOWNLOAD_LOCATION + str(x) + image_url_jpg[-4:]

                    if os.path.isfile(image_name):
                        print('This image is already downloaded')
                    else:
                        download_image(image_url_jpg, image_name)
                    stats['image_src_jpg'] = image_url_jpg
                except TypeError:
                    stats['image_src_jpg'] = None
                    pass

                try:
                    image_url_png = soup.find('a', id='png')['href']

                    image_name = YANDERE_DOWNLOAD_LOCATION + str(x) + image_url_png[-4:]

                    if os.path.isfile(image_name):
                        print('This image is already downloaded')
                    else:
                        download_image(image_url_png, image_name)
                    stats['image_src_png'] = image_url_png
                except TypeError:
                    stats['image_src_png'] = None
                    pass

                statistics = soup.find('div', id="stats")
                all_li = statistics.find_all('li')

                # get the image id
                stats['id'] = x

                # get the image size
                if 'Size' in str(all_li[2]):
                    stats['resolution'] = all_li[2].text.replace('Size: ', '')

                # get the image rating
                if 'Rating' in str(all_li[3]):
                    stats['rating'] = all_li[3].text.replace('Rating: ', '') 
                elif 'Rating' in str(all_li[2]):
                    stats['rating'] = all_li[2].text.replace('Rating: ', '')

                # get the score of the image
                if 'Score' in str(all_li[4]):
                    stats['score'] = int(re.findall(r'\d+', all_li[4].text)[0])  # Get all digits in a string
                elif 'Score' in str(all_li[3]):
                    try:
                        stats['score'] = int(re.findall(r'\d+', all_li[3].text)[0])  # Get all digits in a string
                    except IndexError:
                        try:
                            if 'Score' in str(all_li[5]):
                                stats['score'] = int(
                                    re.findall(r'\d+', all_li[5].text)[0])  # Get all digits in a string
                        except IndexError:
                            print('\tScore was not found on this post.')
                            pass

                # get the image tags
                links = [tag for tag in soup.find('h5', text='Tags').parent.find_all('a') if '?' not in tag.text]
                tags = defaultdict(list)

                # get every tag and its type
                for link in links:
                    if 'general' in link.parent['class'][0]:
                        tags['general'].append(link.text)
                    elif 'character' in link.parent['class'][0]:
                        tags['character'].append(link.text)
                    elif 'artist' in link.parent['class'][0]:
                        tags['artist'].append(link.text)
                    elif 'copyright' in link.parent['class'][0]:
                        tags['copyright'].append(link.text)
                    elif 'circle' in link.parent['class'][0]:
                        tags['circle'].append(link.text)
                    elif 'faults' in link.parent['class'][0]:
                        tags['faults'].append(link.text)
                    else:
                        print('unknown type')
                stats['tags'] = tags

                # get the number of favorites for the current image
                for li in all_li:
                    if 'Favorited' in li.text:
                        stats['favorites'] = len(li.find_all('a')) - 1

                # If there is a main file work with it
                if os.path.isfile(MAIN_YANDERE_JSON_FILEPATH):
                    with open(MAIN_YANDERE_JSON_FILEPATH, 'r') as json_file:
                        yandere_info = json.loads(json_file.read())
                        yandere_info[x] = stats

                        with open(MAIN_YANDERE_JSON_FILEPATH, 'w') as updated_json_file:
                            updated_json_file.write(json.dumps(yandere_info))

                print(str(x) + ' has been downloaded.\tTime: ' + datetime.now().time().strftime("%H:%M:%S"))

                # smart increment for the next index (skipping the 404 pages, because the website provides a "next"
                # button)
                x = int(re.findall(r'\d+', soup.find('a', text='Next')['href'])[0])

            else:
                print('Status:' + str(page.status_code))
                break
    else:
        print('There is no main file.')
