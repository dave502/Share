from webpage import WebPage
from selenium.webdriver.common.by import By

class YandexSeacrhLocators:
    LOCATOR_YANDEX_INPUT_FIELD = (By.XPATH, '//span[@class="input__box"]/input')
    LOCATOR_YANDEX_SEARCH_BUTTON = (By.XPATH, '//div[@class="search2__button"]/button[@type="submit"]')
    '//a[contains(@href,"tensor.ru")]'
    LOCATOR_YANDEX_INPUT_SUGGESTIONS = (By.XPATH, '//li[contains(@class,"mini-suggest__item")]')
    LOCATOR_YANDEX_SEARCH_RESULTS = (By.XPATH, '//li[@class="serp-item desktop-card"]//a[@role="text"]')
    LOCATOR_YANDEX_NAVIGATION_BAR = (By.XPATH, '//nav')
    LOCATOR_YANDEX_NAVIGATION_LINK = (By.XPATH, '//nav//a[div[contains(text(), __item_text)]]')
    LOCATOR_YANDEX_IMG_CATEGORIES = (By.XPATH, '//div[@data-grid-name="im"]')
    LOCATOR_YANDEX_IMG_LINKS = (By.XPATH, '//a[@class="serp-item__link"]/img')
    LOCATOR_YANDEX_NEXT_IMG = (By.XPATH, '//div[contains(@class, "CircleButton_type_next")]')
    LOCATOR_YANDEX_PREV_IMG = (By.XPATH, '//div[contains(@class, "CircleButton_type_prev")]')

class YandexActions(WebPage):

    def get_input_box(self):
        """
        получить строку поиска
        """
        input_field = self.find_element(YandexSeacrhLocators.LOCATOR_YANDEX_INPUT_FIELD)
        return input_field

    def get_input_box_text(self):
        """
        получить текст из строки поиска
        """
        input_field = self.find_element(YandexSeacrhLocators.LOCATOR_YANDEX_INPUT_FIELD)
        return input_field.get_attribute('value')

    def enter_word(self, word):
        """
        ввести текст в строку посика
        """
        search_field = self.find_element(YandexSeacrhLocators.LOCATOR_YANDEX_INPUT_FIELD)
        search_field.click()
        search_field.send_keys(word)
        return search_field

    def get_suggestions(self):
        """
        получить выпадающие подсказки к строке посика
        """
        search_suggestions = self.find_element(YandexSeacrhLocators.LOCATOR_YANDEX_INPUT_SUGGESTIONS)
        return search_suggestions

    def click_on_the_search_button(self):
        """
        пнажать кнопку посика
        """
        return self.find_element(YandexSeacrhLocators.LOCATOR_YANDEX_SEARCH_BUTTON, time=5).click()

    def get_search_results_links(self, link, limit=5):
        """
        получить результаты поиска содержащие указанную ссылку
        limit - количество получаемых результатов
        """
        search_results = self.find_elements(YandexSeacrhLocators.LOCATOR_YANDEX_SEARCH_RESULTS)
        links = []
        for _, search_item in zip(range(limit), search_results):
            href = search_item.get_attribute('href')
            if link not in href: break
            else: links.append(href)
        return links

    def get_navigation_bar(self):
        """
        получить панель навигации
        """
        nav_bar = self.find_element(YandexSeacrhLocators.LOCATOR_YANDEX_NAVIGATION_BAR)
        return nav_bar

    def get_navigation_link(self, link_text):
        """
        получить элемент панели навигации
        link_text - текст элемента навигации
        """
        locator = (By.XPATH, f'//nav//a/div[contains(text(), "{link_text}")]/..')
        nav_link = self.find_element(locator)
        return nav_link

    def get_images_categories(self):
        """
        получить элементы категорий изображений
        """
        img_cats = self.find_elements(YandexSeacrhLocators.LOCATOR_YANDEX_IMG_CATEGORIES)
        img_catefories = [{item.get_attribute('data-grid-text'): item.find_element(By.XPATH, './a').get_attribute('href')} for item in img_cats]
        return img_catefories

    def get_thumbs_in_images(self):
        """
        получить элементы изображений
        """
        images = self.find_elements(YandexSeacrhLocators.LOCATOR_YANDEX_IMG_LINKS)
        return images

    def get_image_nav_btns(self):
        """
        получить элементы навигации изображений
        """
        prev_img_btn = self.find_element(YandexSeacrhLocators.LOCATOR_YANDEX_PREV_IMG)
        next_img_btn = self.find_element(YandexSeacrhLocators.LOCATOR_YANDEX_NEXT_IMG)
        return prev_img_btn, next_img_btn

    def get_opened_image_source(self):
        """
        получить источник открытого изображения
        """
        locator = (By.XPATH, f'//img[@class="MMImage-Origin"]')
        source = self.find_element(locator).get_attribute('src')
        return source

    def open_link(self, element):
        """
        открыть ссылку элемента в новой вкладке
        """
        href = element.get_attribute('href')
        return self.open_new_page(href)

    def open_page(self, link):
        """
        открыть ссылку в новой вкладке
        """
        return self.open_new_page(link)





