import sqlite3
from pathlib import Path
import json

DB_PATH = Path(__file__).parent.parent.parent / "data" / "sales.db"

def _connect():
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    return con

    

def get_schema():
    con = _connect()
    cur = con.cursor()
    res = cur.execute("SELECT name, sql FROM sqlite_master WHERE type = 'table';")
    data = res.fetchall()
    joined = "\n\n".join(sql for name, sql in data)
    # close connection
    con.close()
    return joined





    # Practice

    # data2 = res.fetchall()
    # print(data2)
    # data3 = res.fetchmany(3)
    # print(data3)
    # print('description', cur.description)

# print(cur)
# print([m for m in dir(cur) if not m.startswith("_")])




def query_sales(sql, max_rows=50):
  
    if not(sql.strip().upper().startswith("SELECT")):
       return "SQL must be a SELECT query"
    con = _connect()
    cur = con.cursor()
    try:
        res = cur.execute(sql)
        columns = [m[0] for m in cur.description]
        rows = res.fetchmany(max_rows+1)
        rows_truncated = rows[:max_rows]
        truncated = len(rows) > max_rows
    
        # print('columns', columns)
        # print('rows', rows_truncated)
        # print('truncated', truncated)
    
        result = { "columns" : columns, "rows": rows_truncated, "truncated": truncated}
        if truncated: 
            result["note"] =  (f"Results truncated to {max_rows} rows. " "Use aggregation (COUNT, SUM, AVG with GROUP BY) or a narrower WHERE clause " "instead of selecting raw rows.")
        output = json.dumps(result)
    
    
    
    
        return output
    except sqlite3.Error as e:
        return f"SQL error: {e}. Check table and column names with get_schema" 
    finally:
        con.close()

    
  


if __name__ == "__main__":
    print(get_schema())
    print(query_sales("SELECT FROM dealz"))
    # query_sales("SELECT * FROM reps")