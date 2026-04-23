from pathlib import Path
from dotenv import load_dotenv
from src.load import load_config, save_quarantine, insert_raw_file, insert_from_stagging_to_core, truncat_stag
from src.extract import load_csv
from src.validate import validate
from src.copy_io import copy_from_file
from src.connection import get_engine, get_db_config
from src.logger_app import setup_logger

load_dotenv(Path(".env"))
config = load_config()

def main():
    logger = setup_logger("")
    db_config = get_db_config(config)
    engine = get_engine(db_config)
    
    raw_data_path = Path(config["paths"]["raw_data"])
    #nie zapisywać valid_oders do pliku tylko df... pipe line w datafusion... sprawdzic pricing
    #zapis do bucketa. zrobić orkiestracje i do gcp. zapytania sql... zadania z cloude 7 z sql*. znalezc githuba nieinformatyka
    orders_df = load_csv(raw_data_path / config["files"]["orders"])
    valid_orders, quarantine, duplicates = validate(orders_df)

    save_quarantine(quarantine, "quarantine")
    save_quarantine(duplicates, "duplicates")
    
    valid_orders_path = Path("valid_orders.csv")
    valid_orders.to_csv(valid_orders_path, index=False)
    
    try:
        truncat_stag(engine)
        copy_from_file(engine, raw_data_path / config["files"]["products"], table="stag_products")
        copy_from_file(engine, raw_data_path / config["files"]["customers"], table="stag_customers")
        copy_from_file(engine, valid_orders_path, table="stag_orders")
        insert_from_stagging_to_core(engine)
        insert_raw_file(engine, raw_data_path / config["files"]["products"])
    except Exception:
        logger.exception("Pipeline failed during DB load")
        raise
    
if __name__ == "__main__":

    main()
