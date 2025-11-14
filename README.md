## For Windows CommandPrompt not powershell
# 1 Navigate to the project folder (where requirements.txt is)
cd C:\path\to\RAGCast
# 2 Create a virtual environment
python -m venv venv
# 3 Activate the environment
venv\Scripts\activate
# 4 Install all dependencies
pip install -r requirements.txt
# 5 (Optional) Add this environment to Jupyter
pip install ipykernel
python -m ipykernel install --user --name=ragcast --display-name "Python (RAGCast)"


## For Macbook
# 1️⃣ Navigate to the project folder
cd ~/path/to/RAGCast

# 2️⃣ Create a virtual environment
python3 -m venv venv

# 3️⃣ Activate it
source venv/bin/activate

# 4️⃣ Install dependencies
pip install -r requirements.txt

# 5️⃣ (Optional) Add this environment to Jupyter
pip install ipykernel
python3 -m ipykernel install --user --name=ragcast --display-name "Python (RAGCast)"



## When you run and it asks you to choose kernel, choose one tha tis venv