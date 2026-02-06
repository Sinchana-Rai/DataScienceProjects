# Welcome to My Ds Babel
***
My Ds Babel
Subject
1 Solution

My Ds Babel	
Submit directory	.
Submit files	my_ds_babel.py - list_volcano.db - list_fault_lines.csv
Description
Data is the heart of an information system. Converting data from a format to another or migrating them to another database is a critical skill.

It would be great if every information system could speak the same language.

Tower of Babel Your mission will be to help translate from one format to another.
We will work with two popular formats: SQL and CSV.

What is SQL?
It stands for Structured Query Language. It helps you perform queries in a database. The query will have the format of:

SELECT (GET)
INSERT
UPDATE
DELETE
It has a specific syntax:

SELECT * FROM table;
INSERT INTO table_name(id, name) VALUES(1, 'Pacific Ocean');
UPDATE ...
DELETE ...
How to connect to an SQLite database?
Good question. Google might have an answer. :-)

What is CSV?
It stands for Comma Separated Values There are files with multiple lines and columns. Divider are , (comma) and new-line (\n)

id,name
1,Pacific Ocean
2,Atlantic Ocean
3,Indian Ocean
4,Arctic Ocean
5,Southern Ocean
Interesting fact: the Southern Ocean was recognized by the International Hydrographic Organization in 2000. It borders Antarctica in its entirety. wiki link

Example in ruby:

require "sqlite3"
require 'csv'

db = SQLite3::Database.new "volcanos.db"

-- Create a database
rows = db.execute <<-SQL
  create table volcanos (
    volcano_name varchar(100),
    latitude int,
    .... OTHER FIELDS
  );
SQL

csv = File.read('list_volcano.csv')

CSV.parse(csv, headers: true) do |row|
    db.execute "insert into volcanos values ( ?, ?, ?, ?, ?, ? )", row.fields
end

p db.execute( "select * from volcanos" )
Part I SQLtoCSV. We will start with the SQL format to CSV

Your function will receives a connection (an sqlite3 object from import sqlite3 which will be already connected), table_name. Your function will transform the content of table_name to CSV format and return it. (Columns separated by comma and rows separated by \n)

Part II CSVtoSQL Your function will transform the content to SQL format by creating the table_name and adding each row.

Part III a) You will use your function to convert the list of all volcanos from CSV to SQL.

b) You will use your function to convert the list of all fault lines from SQL to CSV. Data are inside the table named: fault_lines.

Technical specifications
Write two functions:

def sql_to_csv(database, table_name):
def csv_to_sql(csv_content, database, table_name):
1# sql_to_csv will receive two strings as parameters and return a string. the database is a filename where sql_to_csv will fetch the information. table_name is the table from the database file to fetch the information. your return value will be a CSV formatted string: "ColA,ColB,ColC\n1,2,3\n4,5,6\n"

2# csv_to_sql will receive three strings as parameters and return nothing. csv_content is a StringIO following the CSV format. the database is a filename where csv_to_sql will push the information. table_name is the table from the database file to insert the data.

DoYourJob libraries are not authorized. We won't list all of them. If you are not doing the sql request by yourself then you are using a "doyourjob library". An example is: sqlalchemy

Example:

print(sql_to_csv('sourse_all_fault_line.db','fault_lines'))

csv_content = open("sourse_list_volcano.csv")
csv_to_sql(csv_content, 'list_volcanos.db','volcanos')
Tip Google: Python sqlite3 Google: Python CSV Google: Python Class Google: SQL Format SELECT Google: create sqlite table Google: SQL Format INSERT

## Task
connect to sqlite and covert CSV to SQL and also SQL to CSV

## Description
we connect to sqlite then read the DB and then convert each row to text then write it to CSV file.
and also in CSV read CSV file using panda and then connect to sqlite and wite the data there.

## Installation
no need to install anything.

## Usage
clone the repo and run the python script. 
you need to give toeach function the requirment arguments

```
./my_project argument1 argument2
```

### The Core Team

