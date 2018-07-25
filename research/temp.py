import pandas
import pickle
import os
import re


path1 = "../assets/edekaData/tx_500_2_df.pkl"
path2 = "../assets/müllerData/tx_98_2_df.pkl"
with open(path1, "rb") as infile:
    df = pickle.load(infile)
    print(df.to_string())