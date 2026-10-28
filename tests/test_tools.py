from sales_agent.tools import get_schema, query_sales
import json
def test_schema_lists_both_tables():
    schema = get_schema()
    assert "CREATE TABLE reps" in schema
    assert "CREATE TABLE deals" in schema

def test_small_query():
    result = json.loads(query_sales("SELECT * FROM reps"))

    assert len(result['rows']) == 12
    col_names = ["rep_id", "name", "region", "quarterly_quota"]
    assert result['columns'] == col_names
    assert not result['truncated']


def test_large_query():
    result = json.loads(query_sales("SELECT * FROM deals"))

    assert len(result['rows']) == 50

    col_names = ["deal_id", "account", "rep_id", "product", "stage", "amount", "created_date", "close_date"]
    assert result['columns'] == col_names
    assert result['truncated']
    assert "50 rows" in result['note']
    

def test_cap_matches_max_rows():
    result = json.loads(query_sales("SELECT * FROM deals", 5))
    
    assert len(result['rows']) == 5

    col_names = ["deal_id", "account", "rep_id", "product", "stage", "amount", "created_date", "close_date"]
    assert result['columns'] == col_names
    assert result['truncated']


def test_non_SELECT():
    result = query_sales("DELETE FROM deals", 5)
    assert result == "SQL must be a SELECT query"


def test_bad_table():
    result = query_sales("  select * FROM dealz")
    assert "SQL error" in result

        



def test_lowercase_and_whitespace():
    result = json.loads(query_sales("  select * FROM deals"))
    assert len(result['rows']) == 50    
    col_names = ["deal_id", "account", "rep_id", "product", "stage", "amount", "created_date", "close_date"]
    assert result['columns'] == col_names
    assert result['truncated']
    assert "50 rows" in result['note']
        





