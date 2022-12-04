import json
import requests
from lxml import etree
import pymysql
from pymysql.converters import escape_string
from tqdm import trange
import time

# artworks by genre
# url of genre
url_now = 'https://www.wikiart.org/en/paintings-by-genre?sortby=1'


# 返回通过genre分类的网页连接与此分类下的图片总数
def url_by_genre(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
        (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.56'
    }
    by_genre = []
    req = requests.get(url, headers=headers, timeout=10)
    text = req.text
    tree = etree.HTML(text)
    for i in range(1, 68):
        temp = []
        url_temp = tree.xpath('/html/body/div/div[1]/section/main/ul/li[{}]/a/@href'.format(i))
        url_temp = 'https://www.wikiart.org' + url_temp[0]
        temp.append(url_temp)
        num_temp = int(tree.xpath('/html/body/div[1]/div[1]/section/main/ul/li[{}]/a/sup/text()'.format(i))[0])
        temp.append(num_temp)
        by_genre.append(temp)
    return by_genre


# 返回页面的图片名称和url
def url_page(by_genre, i):
    data = {"select": 'featured',
            "jason": 2,
            "layout": 'new',
            "page": i,
            "resultType": 'masonry'}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.56'
    }
    url = by_genre + '&json=2&layout=new&page=2&resultType=masonry'
    response = requests.get(url, headers=headers, data=data)
    jdata = json.loads(response.content)
    urls = ['https://www.wikiart.org' + i['paintingUrl'] for i in jdata['Paintings']]
    return urls


# print(url_genre(url_now))
# print(url_page(2))
# 返回图片链接
# def url_pic(url):
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
#             (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.56'
#     }
#     req = requests.get(url, headers=headers)
#     text = req.text
#     tree = etree.HTML(text)
#     url_temp = tree.xpath('/html/body/div[2]/div[1]/section[1]/main/div[2]/aside/div[1]/img/@src')
#     return url_temp[0]


# print(url_pic('https://www.wikiart.org/en/fayum-portrait/mummy-portrait-of-a-girl'))

# 返回tag字典
def tag_pic(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.56'
    }
    # 修改重连次数，防止无法连接
    requests.DEFAULT_RETRIES = 5

    req = requests.get(url, headers=headers)
    text = req.text
    tree = etree.HTML(text)
    dict_temp = {
        'Name': '',
        'Artist': '',
        'Date': '',
        'Style': '',
        'Theme': '',
        'Genre': '',
        'Media': '',
        'Location': '',
        'Dimensions': '',
        'Introduction': '',
        'Url': ''
    }
    # 作品名
    name = tree.xpath('/html/body/div[2]/div[1]/section[1]/main\
                            /div[2]/article/h3/text()')[0]
    dict_temp['Name'] = name

    # 作者
    artist = tree.xpath('/html/body/div[2]/div[1]/section[1]/main\
                        /div[2]/article/h5/span/a/text()')[0]
    dict_temp['Artist'] = artist

    # 图片链接
    url_pic = tree.xpath('/html/body/div[2]/div[1]/section[1]/main\
                        /div[2]/aside/div[1]/img/@src')[0]
    dict_temp['Url'] = url_pic

    # 简介
    introductions = []
    introduction = tree.xpath('/html/body/div[2]/div[1]/section[1]/main\
                                    /div[2]/div[1]/div[2]/p[1]/text()[1]')
    i = 1
    while introduction:
        if introduction != ['\r']:
            introductions += introduction
        i += 1
        introduction = tree.xpath('/html/body/div[2]/div[1]/section[1]/main\
                                    /div[2]/div[1]/div[2]/p[1]/text()[{}]'.format(i))
    intro = '\n'.join(introductions)
    dict_temp['Introduction'] = intro

    # 其余tag
    # 对不同的li进行尝试
    i = 1
    while True:
        key = ''
        val_temp = ''
        # 标头为 li 的元素
        try:
            # key
            key = str(tree.xpath('/html/body/div[2]/div[1]/section[1]/main\
                    /div[2]/article/ul/li[{}]/s/text()'.format(i))[0])
            key = key[0: len(key) - 1]

            # value
            if key == 'Date':
                val_temp = str(tree.xpath('/html/body/div[2]/div[1]/section[1]/main\
                                /div[2]/article/ul/li[{}]/span/text()'.format(i))[0])
            elif key == 'Style':
                val_temp = str(tree.xpath('/html/body/div[2]/div[1]/section[1]/main\
                                /div[2]/article/ul/li[{}]/span/a/text()'.format(i))[0])
            elif key == 'Theme':
                val_temp = str(tree.xpath('/html/body/div[2]/div[1]/section[1]/main\
                                /div[2]/article/ul/li[{}]/a/text()'.format(i))[0])
            elif key == 'Genre':
                genre_lst = tree.xpath('//html/body/div[2]/div[1]/section[1]/main\
                                /div[2]/article/ul/li[{}]/span/a/span/text()'.format(i))
                val_temp = ', '.join(genre_lst)
            elif key == 'Media':
                val_temp = str(tree.xpath('/html/body/div[2]/div[1]/section[1]/main\
                                /div[2]/article/ul/li[{}]/span/a/text()'.format(i))[0])
            elif key == 'Location':
                val_temp = str(tree.xpath('/html/body/div[2]/div[1]/section[1]/main\
                                /div[2]/article/ul/li[{}]/span/text()'.format(i))[0])
            elif key == 'Dimensions':
                val_temp = str(tree.xpath('/html/body/div[2]/div[1]/section[1]/main\
                                /div[2]/article/ul/li[{}]/text()'.format(i))[1])
            else:
                i += 1
                continue
            val_temp = val_temp.replace("\n", '')
            val_temp = val_temp.strip()
            dict_temp[key] = val_temp

        except:
            break

        i += 1

    return dict_temp


def introduction_pic(page):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                    (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.56'
    }
    # 修改重连次数，防止无法连接
    requests.DEFAULT_RETRIES = 5
    req = requests.get(page, headers=headers)
    text = req.text
    tree = etree.HTML(text)
    introductions = []
    introduction = tree.xpath('/html/body/div[2]/div[1]/section[1]/main\
                                /div[2]/div[1]/div[2]/p[1]/text()[1]')
    i = 1
    while introduction:
        if introduction != ['\r']:
            introductions += introduction
        i += 1
        introduction = tree.xpath('/html/body/div[2]/div[1]/section[1]/main\
                                /div[2]/div[1]/div[2]/p[1]/text()[{}]'.format(i))
    introductions = '\n'.join(introductions)
    return introductions


# 开爬
if __name__ == '__main__':
    conn = pymysql.connect(host='localhost', user='root', password='123456', db='test')
    mycursor = conn.cursor()
    print('OK')
    # 创建SQL语句
    sql = "INSERT INTO wikiart_test (Name, Artist, Date, Style, Theme, Genre, Media, Location,\
            Dimensions, Introduction, Url)VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    by_genres = url_by_genre(url_now)
    genre_num = 0
    while genre_num < len(by_genres):
        by_genre = by_genres[genre_num]
        url = by_genre[0]
        num = by_genre[1]

        print('genre_num = {}'.format(genre_num))
        if num >= 3600:
            for i in range(1, 61):
                pages = url_page(url, i)
                print('pages_num = {}'.format(i))
                count = 1
                while count - 1 < len(pages):
                    try:
                        url_temp = pages[count - 1]
                        dict = tag_pic(url_temp)
                        print('pic_num = {}'.format(count))
                        values = list(dict.values())
                        mycursor.execute(sql, values)
                        conn.commit()
                        print("添加成功")
                        count += 1
                    except:
                        print("出现断连，重新执行")
                        time.sleep(1)
                        continue

                time.sleep(1)
        else:
            num_page = num / 60
            for i in range(1, num_page + 1):
                pages = url_page(url, i)
                print('pages_num = {}'.format(i))
                count = 1
                while count - 1 <= len(pages):
                    try:
                        url_temp = pages[count - 1]
                        dict = tag_pic(url_temp)
                        print('pic_num = {}'.format(count))
                        values = list(dict.values())
                        mycursor.execute(sql, values)
                        conn.commit()
                        print("添加成功")
                        count += 1

                    except:
                        print("出现断连，重新执行")
                        time.sleep(1)
                        continue

        genre_num += 1

    conn.close()
