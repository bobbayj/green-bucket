#%%
# Initialise libraries
import os
import numpy as np
import csv

print(os.getcwd())

# Import securities csv and store in list
stocks = []

with open('stocks_list.csv', encoding='utf-8-sig') as file:
    reader = csv.reader(file)
    stocks = list(reader)

    stocks = [item for sublist in stocks for item in sublist]   # Collapse the list

# For each stock, get historical data and store
x = stocks[0]



#%%