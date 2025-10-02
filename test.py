from sqlalchemy import *
import psycopg2

print("Connecting")
#conn_string = "host='34.148.223.31' dbname='proj1part2' user='sa4564' password='521455' port='5432' connect_timeout=5"

engine = create_engine("postgresql://sa4564:521455@34.148.223.31:5432/proj1part2")
with engine.connect() as conn:
    result = conn.execute(text("select * from passenger"))

#conn=psycopg2.connect(conn_string)

#cur=conn.cursor()

#ur.execute("Select * From flight")

#rows=cur.fetchall()

for row in result:
    print (row)

#for row in rows:
 #   print(row)

#cur.close()

#conn.close()
print("Connected")

# engine = create_engine()