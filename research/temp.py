import pandas as pd

df = pd.read_pickle("../data/tx_100_2_df.pkl")
print(df.to_string())