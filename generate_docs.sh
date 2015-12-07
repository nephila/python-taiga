export LC_ALL=en_US.UTF-8

rm -rf docs/build/.doctrees docs/build/_sources docs/build/static docs/build/.buildinfo
rm -rf docs/build/*.*

pip install . --upgrade

sphinx-build -b html docs/ docs/build

mv docs/build/_static docs/build/static

sed -i '' 's/_static/static/g' docs/build/index.html

pip uninstall python-taiga --yes
