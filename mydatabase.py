from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Date, Float, String, MetaData
from sqlalchemy.ext.declarative import declarative_base


# Global Variables
SQLITE = 'sqlite'

class MyDatabase:
    # http://docs.sqlalchemy.org/en/latest/core/engines.html
    DB_ENGINE = {
        SQLITE: 'sqlite:///{DB}'
    }

    # Main DB Connection Ref Obj
    db_engine = None
    metadata = None
    def __init__(self, dbtype, username='', password='', dbname=''):
        dbtype = dbtype.lower()
        if dbtype in self.DB_ENGINE.keys():
            engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)
            self.db_engine = create_engine(engine_url)
            self.metadata = MetaData()
            self.metadata.reflect(bind=self.db_engine)
            print(self.db_engine)
        else:
            print("DBType is not found in DB_ENGINE")

    # Insert, Update, Delete
    def execute_query(self, query=''):
        if query == '' : return
        print (query)
        with self.db_engine.connect() as connection:
            try:
                connection.execute(query)
            except Exception as e:
                print(e)

    def create_db_table(self, name):
        tables = self.metadata.tables.keys()
        if name not in tables:
            try:
                table = Table(name, self.metadata,
                            Column('date',Date,primary_key=True),
                            Column('code',String),
                            Column('open',Float),
                            Column('high',Float),
                            Column('low',Float),
                            Column('close',Float),
                            Column('volume',Float))
                table.create(self.db_engine)
                print("Tables created")
            except Exception as e:
                print("Error occurred during Table creation!")
                print(e)

    def print_all_data(self, table='', query=''):
        query = query if query != '' else "SELECT * FROM '{}';".format(table)
        print(query)
        with self.db_engine.connect() as connection:
            try:
                result = connection.execute(query)
            except Exception as e:
                print(e)
            else:
                for row in result:
                    print(row) # print(row[0], row[1], row[2])
                result.close()
        print("\n")