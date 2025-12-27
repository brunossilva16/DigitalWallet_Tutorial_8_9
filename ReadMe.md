# Commands Used

pip3 install pynguin

venv\Scripts\activate

$env:PYNGUIN_DANGER_AWARE=1

pynguin --project-path . --module-name src.wallet --output-path tests

pip install pytest

$env:PYTHONPATH = "$PWD"
pytest tests/


pytest tests/

coverage run --branch -m pytest tests/test_src_wallet.py

coverage report -m

---- WSL ----

wsl -u root

pip install pytest mutmut coverage

run mutmut

mutmut results

mutmut run --paths-to-mutate src/wallet_system.py --runner "pytest test/test_src_wallet_llm.py -x"