from yandex import YandexActions


class TestYandex:

    def test_1(self, browser):
        yandex_main_page = YandexActions(browser)
        yandex_main_page.go_to_site()
        yandex_main_page.get_input_box()
        yandex_main_page.enter_word("Тензор")
        yandex_main_page.get_suggestions()
        yandex_main_page.click_on_the_search_button()
        limit = 5
        links = yandex_main_page.get_search_results_links("tensor.ru", limit)
        assert len(links) == limit

    def test_2(self, browser):
        yandex_main_page = YandexActions(browser)
        yandex_main_page.go_to_site()
        nav_images_link = yandex_main_page.get_navigation_link('Картинки')
        yandex_main_page.open_link(nav_images_link)

        assert "https://yandex.ru/images/" in browser.current_url
        # получаем список категорий изображений
        img_cats = yandex_main_page.get_images_categories()
        # получаем ссылку на первую категорию
        first_cat_link = list(img_cats[0].values())[0]
        # открываем ссылку и переходим на новую открывшуюся вкладку
        yandex_main_page.open_page(first_cat_link)
        # проверка совпадения адреса новой вкладки со ссылкой категории
        assert browser.current_url == first_cat_link
        # получаем текст из строки поиска
        input_text = yandex_main_page.get_input_box_text()
        # сравниваем текст поиска с названием первой категории
        first_cat_text = list(img_cats[0].keys())[0]
        assert input_text == first_cat_text
        # получаем элементы изображений
        thumbs = yandex_main_page.get_thumbs_in_images()
        # открываем первое изображение
        thumbs[0].click()
        # получаем адрес источника открытого изображения
        img_1_src = yandex_main_page.get_opened_image_source()
        # проверяем наличие адреса, т.е. открылось ли изображение
        assert img_1_src is not None
        # получаем кнопки навигации по изображениям
        prev_img_btn, next_img_btn = yandex_main_page.get_image_nav_btns()
        # нажимаем на кнопку следующего изображения
        next_img_btn.click()
        # получаем адрес источника открытого изображения
        img_2_src = yandex_main_page.get_opened_image_source()
        # проверяем наличие адреса, т.е. открылось ли изображение
        assert img_2_src is not None
        # нажимаем на кнопку предыдущего изображения
        prev_img_btn.click()
        # получаем адрес источника открытого изображения
        img_3_src = yandex_main_page.get_opened_image_source()
        # проверяем равенство ссылок первого открытого изображения и того же изображения после навигации
        assert img_3_src == img_1_src




