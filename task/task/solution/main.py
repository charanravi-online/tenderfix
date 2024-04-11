from fastapi import FastAPI, HTTPException, Response, File, UploadFile
import pandas as pd
import sqlite3
import json
import re
from pdfquery import PDFQuery
import csv
import os

app = FastAPI()

# Function to push data from CSV files to SQLite database
def push_data_to_sqlite():
    # Read CSV files into DataFrame
    lookup_df = pd.read_csv('lookup.csv')
    products_df = pd.read_csv('mapToProducts.csv')

    # Connect to SQLite database
    conn = sqlite3.connect('data.db')

    # Convert DataFrame to SQL table
    lookup_df.to_sql('lookup', conn, if_exists='replace', index=False)
    products_df.to_sql('products', conn, if_exists='replace', index=False)

    # Close the database connection
    conn.close()

# Call the function to initialize the database
push_data_to_sqlite()

# Load the lookup mapping as a Python dictionary for quick access
def load_lookup_mapping():
    # Connect to SQLite database
    conn = sqlite3.connect('data.db')

    # Execute SQL query to select necessary columns
    lookup_mapping = pd.read_sql_query("SELECT assigned_integer, belegnummer FROM lookup", conn)

    # Close the database connection
    conn.close()

    # Convert DataFrame to dictionary
    return dict(zip(lookup_mapping['belegnummer'], lookup_mapping['assigned_integer']))

# route to fetch entries based on document number
@app.get("/entries/{document_number}", response_class=Response)
async def get_entries(document_number: str):
    conn = sqlite3.connect('data.db')

    # SQL query to fetch related entries from the database
    query = """
    SELECT l.assigned_integer, p.belegnummer, p.posnummer as entry_number, p.artikelnummer as product_numbers
    FROM products p
    JOIN lookup l ON p.belegnummer = l.belegnummer
    WHERE p.belegnummer = ?
    """
    related_entries = pd.read_sql_query(query, conn, params=[document_number])
    conn.close()

    # If no entries found, raise HTTP 404 error
    if related_entries.empty:
        raise HTTPException(status_code=404, detail=f"No entries found for document number {document_number}")
    
    # Convert the DataFrame to CSV format
    output_csv = related_entries.to_csv(index=False)

    # Return the CSV data as a response
    return Response(content=output_csv, media_type="text/csv")


# route to fetch the entire database
@app.get("/database/")
async def get_database():
    conn = sqlite3.connect('data.db')
    lookup_data = pd.read_sql_query("SELECT * FROM lookup", conn)
    products_data = pd.read_sql_query("SELECT * FROM products", conn)
    conn.close()

    # Replace NaN values with None for proper JSON conversion
    lookup_data = lookup_data.where(pd.notnull(lookup_data), None)
    products_data = products_data.where(pd.notnull(products_data), None)

    # Combine the data into a single dictionary
    database_data = {
        'lookup': lookup_data.to_dict(orient='records'),
        'products': products_data.to_dict(orient='records')
    }

    # Convert the dictionary to JSON format and return
    return json.dumps(database_data)

# function to process the pdf files and save the data to a csv file
def process_pdfs_and_save_to_csv(directory_path, output_csv_path):
    # Prepare the CSV file for writing
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["assigned_integer", "entry_number", "entry_body", "quantity"])

        # Iterate over all files in the directory
        for filename in os.listdir(directory_path):
            if filename.lower().endswith(".pdf"):  # Check if the file is a PDF
                pdf_file_path = os.path.join(directory_path, filename)

                try:
                    # Use PDFQuery to extract text from the PDF file
                    pdf = PDFQuery(pdf_file_path)
                    pdf.load()
                    extracted_text = pdf.pq('LTTextLineHorizontal').text()
                    pdf.tree = None  # Release resources

                    # Extract entry numbers, bodies, and quantities
                    entries = re.findall(r'(\d+\.\d+)\.\s(.*?)(\d+,\d+\sSt)', extracted_text, re.DOTALL)

                    for entry_number, entry_body, quantity in entries:
                        entry_body = entry_body.strip()  # Clean up the body text
                        csv_writer.writerow([filename, entry_number, entry_body, quantity])

                except Exception as e:
                    print(f"Error processing {filename}: {e}")


directory_path = './pdfs'  # Path to the directory containing the PDF files
output_csv_path = 'task_2.csv'  # Path where the CSV file will be saved
process_pdfs_and_save_to_csv(directory_path, output_csv_path)