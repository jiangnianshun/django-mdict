file="mdict_path.json"
if [ ! -f $file ]; then
echo "set mdict path and audio path..."
read -p "input mdict path: " mdict_path
if [ $mdict_path ]; then
python3 init_mdict_path.py -m $mdict_path
fi
read -p "input audio path: " audio_path
if [ $audio_path ]; then
python3 init_mdict_path.py -a $audio_path
fi
fi
source init_server_yum.sh
python3 manage.py runserver 0.0.0.0:8000 --noreload