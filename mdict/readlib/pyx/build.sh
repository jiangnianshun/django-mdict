#!/bin/bash
#!/usr/bin/env python3
cd `dirname  $0`
if [ `dirname  $0`="/code" ]; then
cd "/code/mdict/readlib/pyx"
fi
python3 setup.py build_ext --inplace
cd mdict/readlib/pyx
file="../../../../lib"
if [ ! -d $file ]; then
echo "make dir lib"
mkdir $file
fi
echo "copying so files to lib"
for i in `ls`;do
cp $i ../../../../lib/$i
done
cd ../../../
