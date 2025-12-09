"""Check DataFetcher structure"""
from utils.analysis_orchestrator import DataFetcher

df_result = DataFetcher().fetch_and_validate('TCS.NS', False, '30d')
if df_result[0] is not None:
    df = df_result[0]
    print("DataFrame columns:", df.columns.tolist())
    print("First row:")
    print(df.iloc[0])
    print("\nDataFrame shape:", df.shape)
    print("\nDataFrame dtypes:")
    print(df.dtypes)
else:
    print("No data returned")
