import requests
from itertools import count
import math
import time
import os
from terminaltables import SingleTable
from dotenv import load_dotenv


def count_vacancies_total_habr(vacancy_name):
    url = 'https://career.habr.com/api/frontend/vacancies'
    params = {
        'q': vacancy_name,
        'locations[]': 'c_678'
        }
    response = requests.get(url, params=params)
    response.raise_for_status()
    vacancies = response.json()
    vacancies_found = vacancies.get('meta').get('totalResults')
    return vacancies_found


def count_vacancies_total_sj(vacancy_name, token):
    url = 'https://api.superjob.ru/2.0/vacancies/'
    params = {
        'keyword': vacancy_name,
        'town': 'Москва',
        'catalogues': 48,
        }
    headers = {
        'X-Api-App-Id': token,
        'Content-Type': 'application/json'
    }
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    vacancies_all_count = response.json().get('total')
    return vacancies_all_count


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


def predict_rub_salary_habr(vacancy_name):
    salary_list = []
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
        vacancies_list = vacancies.get('list')
        for vacancy in vacancies_list:
            salary = vacancy.get('salary')
            salary_currency = salary.get('currency')
            salary_from = salary.get('from')
            salary_to = salary.get('to')
            if salary_currency == 'rur':
                mean_salary = predict_salary(salary_from, salary_to)
                salary_list.append(mean_salary)
    salary_list = [salary for salary in salary_list if salary is not None]
    return salary_list


def predict_rub_salary_sj(vacancy_name, token):
    vacancies_per_page = 100
    salary_list = []
    for page in count(0):
        url = 'https://api.superjob.ru/2.0/vacancies/'
        params = {
            'keyword': vacancy_name,
            'town': 'Москва',
            'catalogues': 48,
            'page': page,
            'count': vacancies_per_page
            }
        headers = {
            'X-Api-App-Id': token,
            'Content-Type': 'application/json'
        }
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        vacancies_all = response.json().get('objects')
        vacancies_all_count = response.json().get('total')
        total_pages = math.ceil(vacancies_all_count / vacancies_per_page)
        if page >= total_pages:
            break
        for vacancy in vacancies_all:
            salary_currency = vacancy.get('currency')
            salary_from = vacancy.get('payment_from')
            salary_to = vacancy.get('payment_to')
            if salary_currency == 'rub':
                mean_salary = predict_salary(salary_from, salary_to)
                salary_list.append(mean_salary)
        time.sleep(2)
    salary_list = [salary for salary in salary_list if salary is not None]
    return salary_list


def get_vacancy_stats_habr(keywords):
    vacancy = dict.fromkeys(keywords)
    for key in keywords:
        vacancy_stats = {}
        salary_list = predict_rub_salary_habr(key)
        if salary_list:
            vacancy_stats['vacancies_found'] = count_vacancies_total_habr(key)
            vacancy_stats['vacancies_processed'] = len(salary_list)
            vacancy_stats['average_salary'] = int(sum(salary_list) / len(salary_list))
        else:
            vacancy_stats['vacancies_found'] = count_vacancies_total_habr(key)
            vacancy_stats['vacancies_processed'] = 0
            vacancy_stats['average_salary'] = 0
        vacancy[key] = vacancy_stats
    return vacancy


def get_vacancy_stats_sj(keywords, token):
    vacancy = dict.fromkeys(keywords)
    for key in keywords:
        vacancy_stats = {}
        salary_list = predict_rub_salary_sj(key, token)
        if salary_list:
            vacancy_stats['vacancies_found'] = count_vacancies_total_sj(key, token)
            vacancy_stats['vacancies_processed'] = len(salary_list)
            vacancy_stats['average_salary'] = int(sum(salary_list) / len(salary_list))
        else:
            vacancy_stats['vacancies_found'] = count_vacancies_total_sj(key, token)
            vacancy_stats['vacancies_processed'] = 0
            vacancy_stats['average_salary'] = 0
        vacancy[key] = vacancy_stats
    return vacancy


def display_table_output(table_title, vacancy_stats: dict):
    subtitle = ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    stats_list = [subtitle]
    for name, stats in vacancy_stats.items():
        vacancy_stats = []
        vacancy_stats.append(name)
        for stat_values in stats.values():
            vacancy_stats.append(stat_values)
        stats_list.append(vacancy_stats)
    table_instance = SingleTable(stats_list, table_title)
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
