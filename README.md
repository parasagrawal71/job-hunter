# Job Hunter CLI

unzip job-hunter.zip
cd job-hunter

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install

pip install -e .

Run: job-hunter --input companies.csv
