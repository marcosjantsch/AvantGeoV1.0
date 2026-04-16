# -*- coding: utf-8 -*-
"""
config_urls.py — mapeia ANO -> URL do CSV.

Edite este arquivo e substitua as URLs de exemplo pelas URLs reais.
"""
import logging

logger = logging.getLogger(__name__)

CSV_URLS = {
    # Exemplos (troque por URLs reais):
    2010: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2010.csv",
    2011: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2011.csv",
    2012: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2012.csv",
    2013: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2013.csv",
    2014: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2014.csv",
    2015: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2015.csv",
    2016: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2016.csv",
    2017: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2017.csv",
    2018: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2018.csv",
    2019: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2019.csv",
    2020: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2020.csv",
    2021: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2021.csv",
    2022: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2022.csv",
    2023: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2023.csv",
    2024: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2024.csv",
    2025: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2025.csv",
    2026: r"C:/Users/marco/OneDrive/00 - Clima/TEMP/csv/resumo_2026.csv",
   
    }

def load_urls():
    logger.info("URLs de CSV carregadas de config_urls.py.")
    return CSV_URLS

def get_url_by_year(urls_dict, year: int):
    return urls_dict.get(int(year))
