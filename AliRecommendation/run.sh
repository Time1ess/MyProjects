#!/bin/sh

data_file='large_data.csv'
model='GBDT'
sampling_rate=10
training_rate=0.8
threshold=0.8
is_test=0
cache=1
windows_size=5

python3 codes/load_data.py --cache $cache "$data_file"
python3 codes/feature_extract.py --cache $cache $windows_size "$data_file"
python3 codes/model_prediction.py --cache $cache --test $is_test "$data_file" "$model" $sampling_rate $training_rate
