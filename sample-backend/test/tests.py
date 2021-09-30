from requests import get, post, patch, delete

URL = "http://localhost:80/"


class Tester:
    def __init__(self):
        self.tests_successful = 0
        self.tests_performed = 0

    @staticmethod
    def show_all():
        """
        Simply gets all entries from service and prints status code (200 expected) and returned json
        :return: None
        """
        print("\nПолучить все записи")
        result = get(URL + 'user')
        print(result.status_code, result.text)

    def sample_test(self, message: str, resource: str, fun, code_expected=200):
        """
        Creates REST API request to service located at URL address
        :param message: a string to print before performing request (for user readability)
        :param resource: a string indicating a resource located in the service that is being requested
        :param fun: a function with which request is performed (get(), post(), patch() or delete() expected)
        :param code_expected: a string, matching the status code, tester should expect from the service
        :return: None
        """
        result = fun(URL + resource)
        if not message == "":
            print("\n" + message)
            print(result.status_code, result.text)
            self.tests_performed += 1
            if result.status_code == code_expected:
                self.tests_successful += 1
                print("Success")
            else:
                print("Fail")

    def report(self):
        print("Tests performed:", self.tests_performed, "Tests successful:", self.tests_successful)


if __name__ == '__main__':
    tester = Tester()

    # post(URL + "user/1?Pyotr%20Pervy")
    tester.sample_test("Первоначальное заполнение базы", "user/1?title=Pyotr%20Pervy", post, 204)
    # post(URL + "user/2?Aleksandr%20Sergeevich%20Pushkin")
    tester.sample_test("Первоначальное заполнение базы", "user/2?title=Aleksandr%20Sergeevich%20Pushkin", post, 204)

    # Successful

    tester.sample_test("Получить все записи", 'user', get, 200)

    tester.sample_test("Получить одну запись с id=2", 'user/2', get, 200)
    tester.sample_test("Получить одну запись с id=2", 'user/2', get, 200)  # Тест кеша

    tester.sample_test("Создать пользователя с именем '; DROP TABLE IF EXISTS users; --",
                       "user/3?title=%27%3B+DROP+TABLE+IF+EXISTS+users%3B+--", post, 204)  # SQL injection
    tester.show_all()

    tester.sample_test("Изменить запись с id=3", "user/3?title=Mikhail%20Vasilievich%20Lomonosov", patch, 204)
    tester.show_all()

    tester.sample_test("Удалить запись с id=3", "user/3", delete, 204)
    tester.show_all()

    # Rejected

    tester.sample_test("Получить несуществующую запись запись с id=3", "user/3", get, 404)

    tester.sample_test("Создать пользователя с id, который уже существует в базе", "user/2?title=Test", post, 422)

    tester.sample_test("Изменить пользователя, которого не существует в базе", "user/3?title=Test%20Title", patch,
                       404)

    tester.sample_test("Удалить пользователя, которого не существует в базе", "user/3", delete, 404)

    # delete(URL + 'user/2')
    tester.sample_test("", "user/2", delete)  # delete all
    # delete(URL + 'user/1')
    tester.sample_test("", "user/1", delete)
    tester.sample_test("Отобразить пустую базу", "user", get, 404)

    tester.report()
