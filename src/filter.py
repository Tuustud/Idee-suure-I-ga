import sqlite3
import pandas as pd

conn = sqlite3.connect(
    r"C:\Users\sasha\Desktop\groupprog\database.db"
)
time = 0
req1= 0
req2 = 0
location = 0
df = pd.read_sql_query("SELECT * FROM items;", conn)

print("How much time do you have?")
print("1 - 0-15min")
print("2 - 15-45min")
print("3 - 45min-1.5h")
time = input("vali")
if time == "1":
    time = "0-15min"
elif time == "2":
    time = "15-45min"
elif time == "3":
    time = "45min-1.5h"
print("1 - Mitte midagi")
print("2 - Paber ja pliiats")
print("3 - Telefon/arvuti")

req1 = input("Vali: ")

if req1 == "1":
    req1 = ""

elif req1 == "2":
    req1 = "Paber-ja-Pliiats"

elif req1 == "3":
    req1 = "Telefon/Arvuti"

print("1 - Mitte midagi")
print("2 - Wi-Fi/andmeside")
print("3 - Teine inimene")

req2 = input("Vali: ")

if req2 == "1":
    req2 = ""

elif req2 == "2":
    req2 = "Wi-Fi/andmeside"

elif req2 == "3":
    req2 = "teine inimene"

print("Kus sa oled?")
print("1 - Rahvarohke")
print("2 - Vaba õhk")
print("3 - Pole tähtis")

location = input("Vali: ")

if location == "1":
    location = "rahvarohke"

elif location == "2":
    location = "vaba õhk"

elif location == "3":
    location = ""

results = df[
    (df["time"] == time) &
    (df["requires1"] == req1) &
    (df["requires2"] == req2) &
    (df["location"] == location)
]


print(results["instructions"])

conn.close()