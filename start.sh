#!/bin/sh
if [ ! -d "./venv" ]
then
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
    echo "Venv setup Done!"
fi

if [ $# -eq 0 ]
then 
	./venv/bin/python3 planesNearby.py
else
./venv/bin/python3 planesNearby.py --mode online --place $1
fi

