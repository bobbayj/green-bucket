from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Date, Float, String, MetaData
from sqlalchemy.ext.declarative import declarative_base


# Global Variables
Base = declarative_base()
SQLITE = 'sqlite'

class MyDatabase:
    # http://docs.sqlalchemy.org/en/latest/core/engines.html
    DB_ENGINE = {
        SQLITE: 'sqlite:///{DB}'
    }

    # Main DB Connection Ref Obj
    db_engine = None
    def __init__(self, dbtype, username='', password='', dbname=''):
        dbtype = dbtype.lower()
        if dbtype in self.DB_ENGINE.keys():
            engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)
            self.db_engine = create_engine(engine_url)
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

    def create_db_tables(self):
        metadata = MetaData()
        try:
            metadata.create_all(self.db_engine)
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

# Table definition
class Historicals(Base):
    __tablename__ = 'historicals'
    date = Column(Date, primary_key=True)
    code = Column(String)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    def __repr__(self):
        return "<Historicals(date='%s', code='%s', open='%s', high='%s',low='%s',close='%s',volume='%s')>" % (
            self.date, self.code, self.open, self.high, self.low, self.close, self.volume)