import mysql.connector as msc
import tabulate as tab

db = msc.connect(
    host="167.71.231.52",
    username="project-work",
    password="mySQLpass",
    database="arcade",
)
cursor = db.cursor()
cursor.execute("select * from user")

print(tab.tabulate(cursor))
cursor.close()
db.commit()
