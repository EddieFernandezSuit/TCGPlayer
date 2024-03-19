import pandas as pd

DOWNLOADS_DIRECTORY=pd.read_csv('config.csv')['DOWNLOADS_DIRECTORY'][0]
PROJECT_DIRECTORY=pd.read_csv('config.csv')['PROJECT_DIRECTORY'][0]
