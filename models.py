import sqlite3
conn = sqlite3.connect('events.db')

c = conn.cursor()
c.execute('''
          CREATE TABLE activity
          (
           id INTEGER PRIMARY KEY ASC,
           name varchar(250) NOT NULL
          )
          ''')

c.execute('''
          CREATE TABLE event
          (
           id INTEGER PRIMARY KEY ASC,
           name varchar(250) NOT NULL,
           activity_id INTEGER NOT NULL,
           FOREIGN KEY(activity_id) REFERENCES activity(id)
          )
          ''')

conn.commit()
conn.close()
