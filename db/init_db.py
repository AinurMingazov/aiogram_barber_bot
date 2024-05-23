from pathlib import Path

from sqlalchemy import text

from db_session import sync_session


def fill_db():
    dir_path = Path(__file__).parent.resolve().joinpath('sql_queries')
    for file in list(dir_path.glob('*.sql')):
        execute_sql_file(file)


def execute_sql_file(file_path):
    with open(file_path) as f:
        table_init_queries = f.read()
    table_init_queries = table_init_queries.split(';')
    for table_init_query in table_init_queries:
        sync_session.execute(text(table_init_query))
        sync_session.commit()


if __name__ == '__main__':
    fill_db()
