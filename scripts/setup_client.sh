#/bin/bash
add-apt-repository main
apt-get install python3-pip jq wrk
python3 -m pip install matplotlib seaborn gdown

# download redis
gdown --id 1qp63Ab6I-5tdQ1bU-zivvJ7OqbwNEGm-

if [ -f /usr/local/bin/redis-benchmark ]; then
    echo "redis-benchmark found in /usr/local/bin"
else
    echo "redis-benchmark not found in /usr/local/bin"
    tar -xf 6.2.6.tar.gz
    cd redis-6.2.6;./configure;make -j$(nproc);make install;cd ..
fi

echo off > /sys/devices/system/cpu/smt/control
echo core >/proc/sys/kernel/core_pattern
