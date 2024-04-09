from fastapi import FastAPI, HTTPException
import pandas as pd
import sqlite3

app = FastAPI()

# Function to push data from CSV to SQLite
def push_data_to_sqlite():
    # Load CSV files into DataFrames
    lookup_df = pd.read_csv('lookup.csv')
    products_df = pd.read_csv('mapToProducts.csv')

    # Connect to SQLite database
    conn = sqlite3.connect('data.db')

    # Push lookup data to SQLite
    lookup_df.to_sql('lookup', conn, if_exists='replace', index=False)

    # Push products data to SQLite
    products_df.to_sql('products', conn, if_exists='replace', index=False)

    # Close the connection
    conn.close()

# Initialize SQLite database
push_data_to_sqlite()

# Load mapping from SQLite database
def load_lookup_mapping():
    conn = sqlite3.connect('data.db')
    lookup_mapping = pd.read_sql_query("SELECT assigned_integer, belegnummer FROM lookup", conn)
    lookup_mapping = dict(zip(lookup_mapping['assigned_integer'], lookup_mapping['belegnummer']))
    conn.close()
    return lookup_mapping

@app.get("/entries/")
async def get_entries(document_number: int):
    # Load the lookup mapping from SQLite database
    lookup_mapping = load_lookup_mapping()

    # Check if the document number is in the mapping
    if document_number not in lookup_mapping:
        raise HTTPException(status_code=404, detail="Searched document number not found")

    # Connect to SQLite database
    conn = sqlite3.connect('data.db')
    

    # Query related entries from products table
    query = f"SELECT * FROM products WHERE belegnummer = '{lookup_mapping[document_number]}'"
    related_entries = pd.read_sql_query(query, conn)

    # Close the connection
    conn.close()

    entries_data = []
    for _, row in related_entries.iterrows():
        entry_number = str(row['posnummer'])
        product_numbers = row['artikelnummer']
        entries_data.append({
            'assigned_integer': document_number,
            'belegnummer': lookup_mapping[document_number],
            'entry_number': entry_number,
            'product_numbers': product_numbers
        })

    return entries_data