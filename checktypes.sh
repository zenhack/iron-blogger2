
export MYPYPATH="$(dirname $0)/stubfiles"
mypy -s $@
