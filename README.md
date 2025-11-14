# Repository for Final Project of ENGS 108: Applied Machine Learning (Dartmouth College; Fall 2025)
## 📝 Overview
This project aims to answer the question: Can a model accurately predict the speaker of a line in a musical using only textual data, without musical or contextual cues?

## 🛠️ Virtual Environment Setup (Run Once)
1. Clone repository
2. Open terminal and navigate to the project directory (where requirements.txt is) (cd ...)
3. Create a new virtual environment (Replace second `venv` with your desired virtual environment name if needed)
   - Windows: 'python -m venv venv'
   - Mac/Linux: 'python3 -m venv venv'

## 📦 Package Installation
1. Activate the virtual environment
   - On windows: 'venv\Scripts\activate'
   - On Mac/Linux: '
2. Install necessary packages:
   - With virtual evironment activated, install all required packages using the command:
     'pip install -r requirements.txt'
3. (Optional) Add this environment to Jupyter
   'pip install ipykernel'
   'python -m ipykernel install --user --name=ragcast --display-name "Python (RAGCast)"'

## When you run and it asks you to choose kernel, choose one that is venv

## File Structure
Folder | Description
------------- | -------------
analysis | Files for each type of analysis/modeling done.
data_new | More efficient scraping/cleaning of data used for final dataset.
data_old | Previous cleaning of data.
requirements.txt | List of libraries that need to be installed to run code in this repository

Files in data_new | Description
------------- | -------------
CleaningData.ipynb | File to scrape and clean data.
ExploratoryDataAnalysis.ipynb | Analysis and visualization of the cleaned data
epic_all_songs_lines_allspeakers.csv | Collected data that includes all speakers.
epic_all_songs_lines_trainingdata.csv | Data that does not include speakers with too little lines. The dataset that is used for all the modeling.
