import pandas as pd
from faker import Faker
import random
import csv
from src.load import load_config
from src.extract import read_input, load_csv
from src.validate import validate
from pathlib import Path
from src.logger_app import setup_logger
from src.load import save_qarantine, insert_raw_file, insert_from_stagging_to_core, truncat_stag
from src.copy_io import copy_from_file
from src.connection import get_engine, get_db_config
from dotenv import load_dotenv

config = load_config()
env_path = Path(r".env")
load_dotenv(env_path)

def main():
    db_config = get_db_config(config)
    engine = get_engine(db_config)
    
    raw_data_path = Path(config["paths"]["raw_data"])
    
    #zapis do gita. zapytania sql... zadania z cloude 7 z sql. zalozyc konto gcp znalezc githuba nieinformatyka
    ord = load_csv(raw_data_path / config["files"]["orders"])
    valid_orders, quarantine, duplikaty = validate(ord)
    # print(f"VALID: {len(valid_orders)}")
    # print(f"INVALID: {len(qua)}")
    save_qarantine(quarantine, "qurantine")
    save_qarantine(duplikaty, "duplikaty")
    #print(qua.isna().sum())
    
    valid_orders.to_csv("valid_orders.csv", index=False)
    
    products_path = Path(raw_data_path / config["files"]["products"])
    orders_path = Path(r"F:\ITwork\brudne_dane_z_faker\valid_orders.csv")
    customers_path = Path(raw_data_path / config["files"]["customers"])
    
    truncat_stag(engine)
    copy_from_file(engine, file_path = products_path, table="stag_products")
    copy_from_file(engine, file_path = customers_path, table="stag_customers")
    copy_from_file(engine, file_path = orders_path, table="stag_orders")
    insert_from_stagging_to_core(engine)
    insert_raw_file(engine, products_path) # tylko jako backup
if __name__ == "__main__":

    main()