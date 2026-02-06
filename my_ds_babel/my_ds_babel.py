import os
import sqlite3
import pandas as pd

def sql_to_csv(database, table_name):
    try:
        # Check if DB exists
        if not os.path.exists(database):
            raise FileNotFoundError(f"Database file {database} does not exist")

        # Connect to DB
        conn = sqlite3.connect(database)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            raise sqlite3.OperationalError(f"Table {table_name} does not exist in {database}")

        # Fetch column names /header
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]

        # Fetch all data
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        lines = []
        lines.append(",".join(columns))  # Add header

        for i, row in enumerate(rows, start=1):
            clean = []
            for v in row:
                v = "" if v is None else str(v)
                if "," in v or '"' in v or "\n" in v:
                    v = '"' + v.replace('"', '""') + '"'
                clean.append(v)
            csv_line = ",".join(clean)
            lines.append(csv_line)
            print(f"line#{i} -> {csv_line}")
        conn.close()
        return "\n".join(lines).rstrip("\n")
    except Exception as e:
        print(f"Error in sql_to_csv: {str(e)}")
        raise

def csv_to_sql(csv_content, database, table_name):
    df = pd.read_csv(csv_content)
    with sqlite3.connect(database) as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)


if __name__ == "__main__":
    sql_db = 'all_fault_line.db'
    table = 'fault_lines'
    output_file_name= "test.csv"
    output = sql_to_csv(sql_db,table)

    with open(f'{output_file_name}', 'w') as f:
        f.write(output)

    print("--------------------------------------")
    output= output.split("\n")
    for line in range(len(output)):
        print(f"#{line} -> {output[line]}")