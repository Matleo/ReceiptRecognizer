import pandas
import pickle
import os
import re


path1 = "../assets/müllerData/tx_218_2_df.pkl"
path2 = "../assets/müllerData/tx_257_2_df.pkl"
path3 = "../assets/müllerData/tx_445_2_df.pkl"
with open(path3, "rb") as infile:
    df = pickle.load(infile)
    print(df.to_string())