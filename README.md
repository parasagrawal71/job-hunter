# Job Hunter CLI

unzip job-hunter.zip
cd job-hunter

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install

pip install -e .

Run: 
    [Testing]
    - job-hunter --input companies_test.csv
    - Open frontend/index.html for dashboard

    [All companies list]
    - job-hunter --input companies.csv
    

