from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class WebPage:

    def __init__(self, driver):
        self.driver = driver
        self.base_url = "https://yandex.ru/"

    def find_element(self, locator,time=10):
        return WebDriverWait(self.driver,time).until(EC.presence_of_element_located(locator),
                                                      message=f"Can't find element by locator {locator}")

    def find_elements(self, locator,time=10):
        return WebDriverWait(self.driver,time).until(EC.presence_of_all_elements_located(locator),
                                                      message=f"Can't find elements by locator {locator}")

    def go_to_site(self):
        return self.driver.get(self.base_url)

    def wait_for_page_loads(self,time=10):
        return WebDriverWait(self.driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')

    def open_new_page(self, link, time=10):
        windows_before = self.driver.window_handles
        self.driver.execute_script(f'window.open("{link}","_blank");')
        WebDriverWait(self.driver, 120).until(EC.new_window_is_opened(windows_before))
        wnd_handles = self.driver.window_handles
        window_after = self.driver.window_handles[len(wnd_handles)-1]
        self.driver.switch_to.window(window_after)
        return windows_before, window_after
