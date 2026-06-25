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


def get_vacancies_habr(programming_languages):
    vacancies_all = []
    for page in count(0):
        url = 'https://career.habr.com/api/frontend/vacancies'
        params = {
            'q': programming_languages,
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


def get_vacancies_sj(programming_languages, token):
    vacancies_per_page = 100
    city_code_moskow = 48
    vacancies_all = []
    for page in count(0):
        url = 'https://api.superjob.ru/2.0/vacancies/'
        params = {
            'keyword': programming_languages,
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
        vacancies = response.json()
        vacancies_found = vacancies.get('total')
        total_pages = math.ceil(vacancies_found / vacancies_per_page)
        if page >= total_pages:
            break
        vacancies_on_page = vacancies.get('objects')
        vacancies_all.append(vacancies_on_page)
        time.sleep(2)
    vacancies_found = response.json().get('total')
    return vacancies_all, vacancies_found


def predict_rub_salary_habr(vacancies_all):
    salary_all = []
    for page in vacancies_all:
        for vacancy in page:
            salary = vacancy.get('salary')
            if not salary:
                continue
            salary_currency = salary.get('currency')
            salary_from = salary.get('from')
            salary_to = salary.get('to')
            if salary_currency == 'rur':
                mean_salary = predict_salary(salary_from, salary_to)
                salary_all.append(mean_salary)
    salary_all = [salary for salary in salary_all if salary is not None]
    return salary_all


def predict_rub_salary_sj(vacancies_all):
    salary_all = []
    for page in vacancies_all:
        for vacancy in page:
            if not vacancy:
                continue
            salary_currency = vacancy.get('currency')
            salary_from = vacancy.get('payment_from')
            salary_to = vacancy.get('payment_to')
            if salary_currency == 'rub':
                mean_salary = predict_salary(salary_from, salary_to)
                salary_all.append(mean_salary)
    salary_all = [salary for salary in salary_all if salary is not None]
    return salary_all


def get_vacancy_stats_habr(programming_languages):
    vacancy_stats = dict.fromkeys(programming_languages)
    for programming_language in programming_languages:
        vacancy_stats_value = {}
        vacancies_all, vacancies_found = get_vacancies_habr(programming_language)
        salary_all = predict_rub_salary_habr(vacancies_all)
        if salary_all:
            vacancies_processed = len(salary_all)
            average_salary = int(sum(salary_all) / len(salary_all))
        else:
            vacancies_processed = 0
            average_salary = 0
        vacancy_stats_value = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }
        vacancy_stats[programming_language] = vacancy_stats_value
    return vacancy_stats


def get_vacancy_stats_sj(programming_languages, token):
    vacancy_stats = dict.fromkeys(programming_languages)
    for programming_language in programming_languages:
        vacancy_stats_value = {}
        vacancies_all, vacancies_found = get_vacancies_sj(programming_language, token)
        salary_all = predict_rub_salary_sj(vacancies_all)
        if salary_all:
            vacancies_processed = len(salary_all)
            average_salary = int(sum(salary_all) / len(salary_all))
        else:
            vacancies_processed = 0
            average_salary = 0
        vacancy_stats_value = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }
        vacancy_stats[programming_language] = vacancy_stats_value
    return vacancy_stats


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
    popular_langs = ['JavaScript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'CSS', 'C#']
    habr_stats = get_vacancy_stats_habr(popular_langs)
    super_job_stats = get_vacancy_stats_sj(popular_langs, token)
    display_table_output(' Habr Moscow ', habr_stats)
    display_table_output(' SuperJob Moscow ', super_job_stats)


if __name__ == '__main__':
    main()
