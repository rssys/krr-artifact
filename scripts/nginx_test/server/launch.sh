#!/bin/bash
cores=${1}
mode=${2}
workload=${3}
basedir=${4}

shift
shift

env_vars="KRR_SMP_IMG=${basedir}/bzImageRR KRR_UNI_IMG=${basedir}/bzImageRR \
  KRR_DISK=${basedir}/rootfs-bypass.qcow2 BL_IMG=${basedir}/bzImageNative \
  KBUILD_DISK=${basedir}/rootfs-kbuild.qcow2 "

KRR_SMP_IMG="$basedir/bzImageNative"
QEMU_BIN="$basedir/qemu-tcg-kvm/build/qemu-system-x86_64"

missing_duration=120
file="/dev/shm/record"

rm -f ${basedir}/test.sock
python3 -c "import socket as s; sock = s.socket(s.AF_UNIX); sock.bind('${basedir}/test.sock')"

exec_qemu() {
  cpu_num=$1
  param="nginx"
  image=${KRR_SMP_IMG}
  branch="native"
  ignore_record="-ignore-record 1"
  ivshmem=""
  rm -f /dev/shm/record
  if [ $mode == "krr" ];then
    param="${param} krr"
    image="$basedir/bzImageRR"
    branch="rr-para"
    ignore_record=""
    ivshmem="-object memory-backend-file,size=32768M,share,mem-path=/dev/shm/ivshmem,id=hostmem -device ivshmem-plain,memdev=hostmem"
  fi

  rm -f $file
  rm -f rr-cost.txt kernel_rr.log
  echo "cores=${cpu_num}, image=${image}, mode=${mode}, ignore-record=${ignore_record}"
  if pgrep qemu > /dev/null; then
      kill -9 $(pgrep qemu)
      echo "qemu process killed"
  else
      echo "No qemu process found"
  fi
  rm -f /dev/shm/ivshmem
  cd $basedir/kernel-rr-linux;git checkout ${branch};sh replace.sh;cd ..
  sync
  echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null
  

  ${QEMU_BIN} -smp $cpu_num -kernel ${image} \
  -accel kvm -cpu host -m 8G -mem-path /mnt/huge -mem-prealloc \
  -append  "root=/dev/sda rw init=/lib/systemd/systemd clocksource=tsc tsc=reliable console=ttyS0 random.trust_cpu=on ${param}" \
  -hda ${basedir}/rootfs-redis.img ${ignore_record} -exit-record 1 \
  -device vfio-pci,host=18:00.1  -D rec.log -qmp unix:${basedir}/test.sock,server=on,wait=off ${ivshmem} -vnc :0 \
  -checkpoint-interval 0 &

  timer=0

  sleep 20

  rr_set_cpu_aff

  while true; do
    if pgrep qemu > /dev/null; then
      true
    else
      echo "Test finished"
      return 0
    fi

    if [ $mode == "baseline" ];then
      sleep 1
      continue
    fi

    if [ -f "$file" ]; then
        # If the file exists, reset the timer
        timer=0
    else
        # If the file does not exist, increment the timer
        ((timer++))
        sleep 1
    fi
  done
}

while true; do
    exec_qemu $cores
    # if [ ${mode} == "krr" ];then
    #     python3 get_cost.py ${mode} ${cores} ${workload}
    # fi
    if [ $? -eq 0 ]; then
        echo "The function returned 0 - success."
        break
    else
        echo "The function returned non-0 - failure."
        exit 1
    fi
done
