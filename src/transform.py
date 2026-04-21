import pandas as pd

def data_cleaning(df):
    df.columns = (
    df.columns
    .str.strip()  
    .str.lower()   
    .str.replace(" ", "_")  
)
