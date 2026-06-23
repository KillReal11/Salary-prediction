import requests
from itertools import count
import math
import time
import os
from terminaltables import SingleTable
from dotenv import load_dotenv


def predict_salary(salary_from, salary_to):
    if not salary_from and not salary_to:
        return None
    if salary_from and salary_to:
        mean_salary = (salary_from + salary_to)/2
    if salary_from and not salary_to:
        calc_coef_from = 1.2
        mean_salary = salary_from * calc_coef_from
    if not salary_from and salary_to:
        calc_coef_to = 0.8
        mean_salary = salary_to * calc_coef_to
    return mean_salary


def get_vacancies_habr(vacancy_name):
    vacancies_all = []
    for page in count(0):
        url = 'https://career.habr.com/api/frontend/vacancies'
        params = {
            'q': vacancy_name,
            'page': page,
            'locations[]': 'c_678'
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        vacancies = response.json()
        total_pages = vacancies.get('meta').get('totalPages')
        if page >= total_pages:
            break
        vacancies_on_page = vacancies.get('list')
        vacancies_all.append(vacancies_on_page)
    vacancies_found = vacancies.get('meta').get('totalResults')
    return vacancies_all, vacancies_found


def get_vacancies_sj(vacancy_name, token):
    vacancies_per_page = 100
    city_code_moskow = 48
    vacancies_all = []
    for page in count(0):
        url = 'https://api.superjob.ru/2.0/vacancies/'
        params = {
            'keyword': vacancy_name,
            'town': 'Москва',
            'catalogues': city_code_moskow,
            'page': page,
            'count': vacancies_per_page
        }
        headers = {
            'X-Api-App-Id': token,
            'Content-Type': 'application/json'
        }
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        vacancies_found = response.json().get('total')
        total_pages = math.ceil(vacancies_found / vacancies_per_page)
        if page >= total_pages:
            break
        vacancies_on_page = response.json().get('objects')
        vacancies_all.append(vacancies_on_page)
        time.sleep(2)
    vacancies_found = response.json().get('total')
    return vacancies_all, vacancies_found


def predict_rub_salary_habr(vacancy_name):
    vacancies_all, __ = get_vacancies_habr(vacancy_name)
    salary_all = []
    for page in vacancies_all:
        for vacancy in page:
            salary = vacancy.get('salary')
            salary_currency = salary.get('currency')
            salary_from = salary.get('from')
            salary_to = salary.get('to')
            if salary_currency == 'rur':
                mean_salary = predict_salary(salary_from, salary_to)
                salary_all.append(mean_salary)
    salary_all = [salary for salary in salary_all if salary is not None]
    return salary_all


def predict_rub_salary_sj(vacancy_name, token):
    salary_all = []
    vacancies_all, __ = get_vacancies_sj(vacancy_name, token)
    for page in vacancies_all:
        for vacancy in page:
            salary_currency = vacancy.get('currency')
            salary_from = vacancy.get('payment_from')
            salary_to = vacancy.get('payment_to')
            if salary_currency == 'rub':
                mean_salary = predict_salary(salary_from, salary_to)
                salary_all.append(mean_salary)
    salary_all = [salary for salary in salary_all if salary is not None]
    return salary_all


def get_vacancy_stats_habr(vacancy_name):
    vacancy = dict.fromkeys(vacancy_name)
    for name in vacancy_name:
        vacancy_stats = {}
        salary_all = predict_rub_salary_habr(name)
        __, vacancies_found = get_vacancies_habr(name)
        if salary_all:
            vacancy_stats = {
                'vacancies_found': vacancies_found,
                'vacancies_processed': len(salary_all),
                'average_salary': int(sum(salary_all) / len(salary_all))
            }
        else:
            vacancy_stats = {
                'vacancies_found': vacancies_found,
                'vacancies_processed': 0,
                'average_salary': 0
            }
        vacancy[name] = vacancy_stats
    return vacancy


def get_vacancy_stats_sj(vacancy_name, token):
    vacancy = dict.fromkeys(vacancy_name)
    for name in vacancy_name:
        vacancy_stats = {}
        salary_all = predict_rub_salary_sj(name, token)
        __, vacancies_found = get_vacancies_sj(name, token)
        if salary_all:
            vacancy_stats = {
                'vacancies_found': vacancies_found,
                'vacancies_processed': len(salary_all),
                'average_salary': int(sum(salary_all) / len(salary_all))
            }
        else:
            vacancy_stats = {
                'vacancies_found': vacancies_found,
                'vacancies_processed': 0,
                'average_salary': 0
            }
        vacancy[name] = vacancy_stats
    return vacancy


def display_table_output(table_title, vacancy_stats: dict):
    subtitle = ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    stats_all = [subtitle]
    for name, stats in vacancy_stats.items():
        vacancy_stats = []
        vacancy_stats.append(name)
        for stat_values in stats.values():
            vacancy_stats.append(stat_values)
        stats_all.append(vacancy_stats)
    table_instance = SingleTable(stats_all, table_title)
    table_instance.justify_columns[2] = 'right'
    print(table_instance.table)
    print()


def main():
    load_dotenv()
    token = os.getenv("SUPERJOB_API_KEY")
    popular_lang = ['JavaScript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'CSS', 'C#']
    habr_stats = get_vacancy_stats_habr(popular_lang)
    super_job_stats = get_vacancy_stats_sj(popular_lang, token)
    display_table_output(' Habr Moscow ', habr_stats)
    display_table_output(' SuperJob Moscow ', super_job_stats)


if __name__ == '__main__':
    main()
