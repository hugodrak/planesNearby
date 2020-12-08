#!/bin/sh
if [ ! -d "./venv" ]
then
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
    echo "Venv setup Done!"
fi
./venv/bin/python3 planesNearby.py --mode online
