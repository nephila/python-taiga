rm -rf docs/build/

pip install . --upgrade

sphinx-build -b html docs/ docs/build
