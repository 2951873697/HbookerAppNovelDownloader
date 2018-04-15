from instance import *
from bookshelf import *
import HbookerAPI
import re


def refresh_bookshelf_list():
    response = HbookerAPI.BookShelf.get_shelf_list()
    if response.get('code') == '100000':
        Vars.cfg.data['shelf_list'] = response['data']['shelf_list']
        Vars.cfg.save()
        BookShelfList.clear()
        for shelf in Vars.cfg.data['shelf_list']:
            BookShelfList.append(BookShelf(shelf))
    for shelf in BookShelfList:
        shelf.show_info()
    if len(BookShelfList) == 1:
        shell_bookshelf(['bookshelf', '1'])
    else:
        print('[提示]', '可输入"bookshelf <书架编号>"来选择/切换书架')


def shell_login(inputs):
    if len(inputs) >= 3:
        response = HbookerAPI.SignUp.login(inputs[1], inputs[2])
        if response.get('code') == '100000':
            Vars.cfg.data['reader_name'] = response['data']['reader_info']['reader_name']
            Vars.cfg.data['user_code'] = response['data']['user_code']
            Vars.cfg.data['common_params'] = {'login_token': response['data']['login_token'],
                                              'account': response['data']['reader_info']['account']}
            Vars.cfg.save()
            HbookerAPI.setcommonparams(Vars.cfg.data['common_params'])
            print('[提示]', '登录成功, 当前用户昵称为:', Vars.cfg.data['reader_name'])
        else:
            print('[提示]', response.get('tip'))
    else:
        print('[提示]', '请输入正确的参数')


def shell_config(inputs):
    if len(inputs) >= 2:
        if inputs[1].startswith('l'):
            Vars.cfg.load()
            print('[提示]', '配置文件已重新加载')
            if Vars.cfg.data.get('user_code') is not None:
                HbookerAPI.setcommonparams(Vars.cfg.data['common_params'])
        elif inputs[1].startswith('sa'):
            Vars.cfg.save()
            print('[提示]', '配置文件已保存')
        elif inputs[1].startswith('se'):
            if len(inputs) >= 3:
                Vars.cfg[inputs[2]] = inputs[3]
            else:
                Vars.cfg[inputs[2]] = None
            print('[提示]', '配置项已修改')
    else:
        print('[提示]', 'config:', str(Vars.cfg.data))


def shell_bookshelf(inputs):
    if len(inputs) >= 2:
        try:
            Vars.current_bookshelf = get_bookshelf_by_index(inputs[1])
            if Vars.current_bookshelf is None:
                print('[提示]', '请输入正确的参数')
            else:
                print('[提示]', '已经选择书架: "' + Vars.current_bookshelf.shelf_name + '"')
                Vars.current_bookshelf.get_book_list()
                Vars.current_bookshelf.show_book_list()
                print('[提示]', '可输入"book <书籍编号>"来选择一本书籍并输入"download <起始章节> <终止章节>"来下载该书籍')
        except Exception as e:
            print('[错误]', e)
            print('选择书架时出错')
    else:
        refresh_bookshelf_list()


def shell_books(inputs):
    if len(inputs) >= 2:
        try:
            Vars.current_book = Vars.current_bookshelf.get_book(inputs[1])
            if Vars.current_book is None:
                response = HbookerAPI.Book.get_info_by_id(inputs[1])
                if response.get('code') == '100000':
                    Vars.current_book = Book(None, response['data']['book_info'])
                else:
                    print('[提示]', '获取书籍信息失败, book_id:', inputs[1])
                    return
            print('[提示]', '已经选择书籍《' + Vars.current_book.book_name + '》')
            Vars.current_book.get_division_list()
            Vars.current_book.get_chapter_catalog()
            Vars.current_book.show_division_list()
            Vars.current_book.show_chapter_latest()
        except Exception as e:
            print('[错误]', e)
            print('选择书籍时出错')
    else:
        if Vars.current_bookshelf is None:
            print('[提示]', '未选择书架')
        else:
            Vars.current_bookshelf.get_book_list()
            Vars.current_bookshelf.show_book_list()


def shell_download(inputs):
    if Vars.current_book is None:
        print('[提示]', '未选择书籍')
        return
    if inputs.count('-a') > 0:
        try:
            for book in Vars.current_bookshelf.BookList:
                book.download_chapter(copy_dir=os.getcwd() + '/../Hbooker/downloads')
                if Vars.cfg.data.get('downloaded_book_id_list') is None:
                    Vars.cfg.data['downloaded_book_id_list'] = []
                Vars.cfg.data['downloaded_book_id_list'].append(book.book_id)
        except Exception as e:
            print('[错误]', e)
            print('下载书架全部书籍时出错')
        finally:
            return
    if inputs.count('-d') > 0:
        try:
            if len(inputs) > inputs.index('-d') + 1:
                Vars.current_book.download_division(inputs[inputs.index('-d') + 1])
            else:
                print('-d 参数出错')
        except Exception as e:
            print('[错误]', e)
            print('下载书籍分卷时出错')
        finally:
            return
    chapter_index_start = None
    chapter_index_end = None
    if inputs.count('-s') > 0:
        try:
            chapter_index_start = inputs[inputs.index('-s') + 1]
        except Exception as e:
            print('[错误]', e)
            print('-s 参数出错')
    if inputs.count('-e') > 0:
        try:
            chapter_index_end = inputs[inputs.index('-e') + 1]
        except Exception as e:
            print('[错误]', e)
            print('-e 参数出错')
    Vars.current_book.download_chapter(chapter_index_start, chapter_index_end)
    if Vars.cfg.data.get('downloaded_book_id_list') is None:
        Vars.cfg.data['downloaded_book_id_list'] = []
    Vars.cfg.data['downloaded_book_id_list'].append(Vars.current_book.book_id)


def shell_update():
    for book_id in Vars.cfg.data['downloaded_book_id_list']:
        response = HbookerAPI.Book.get_info_by_id(book_id)
        if response.get('code') == '100000':
            Vars.current_book = Book(None, response['data']['book_info'])
            Vars.current_book.get_division_list()
            Vars.current_book.get_chapter_catalog()
            Vars.current_book.download_chapter(copy_dir=os.getcwd() + '/../Hbooker/updates')
        else:
            print('[提示]', '获取书籍信息失败, book_id:', book_id)


def shell():
    for info in Vars.help_info:
        print('[帮助]', info)
    while True:
        try:
            inputs = re.split('\s+', get('>').strip())
            if inputs[0].startswith('l'):
                shell_login(inputs)
            elif inputs[0].startswith('c'):
                shell_config(inputs)
            elif inputs[0].startswith('h'):
                for info in Vars.help_info:
                    print('[帮助]', info)
            elif inputs[0].startswith('books'):
                shell_bookshelf(inputs)
            elif inputs[0].startswith('b'):
                shell_books(inputs)
            elif inputs[0].startswith('d'):
                shell_download(inputs)
            elif inputs[0].startswith('u'):
                shell_update()
        except Exception as e:
            print('[错误]', e)


Vars.cfg.load()
if Vars.cfg.data.get('user_code') is not None:
    HbookerAPI.setcommonparams(Vars.cfg.data['common_params'])
    refresh_bookshelf_list()
shell()
