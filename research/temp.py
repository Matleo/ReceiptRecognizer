import pandas
import pickle

with open("../assets/müllerData/tx_2_2_df.pkl", "rb") as infile:
    df = pickle.load(infile)
    print(df.to_string())