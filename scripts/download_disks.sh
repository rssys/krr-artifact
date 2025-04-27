#!/bin/bash
gdown --id 17LmtsNHwXui3NrP1CWFRM4VPrcEqs7FY # rocsdb disk image
gzip -d rootfs-bypass.qcow2.gz

gdown --id 1USs8dY4O22Xxm_LuxBJYvn7Y6zunVbQa # dpdk disk image
gzip -d rootfs-redis.qcow2.gz

gdown --id 1I3-4OxfwQv33VxfFWvW1ZSWdGxq6llhU # kernel-build image
gzip -d rootfs-kbuild.qcow2.gz

echo "Converting rootfs-redis.qcow2 to raw"
qemu-tcg-kvm/build/qemu-img convert -f qcow2 -O raw rootfs-redis.qcow2 rootfs-redis.img

cd qemu-tcg-kvm/build/; ./qemu-img create nkbypass.img 5G;mkfs.ext4 nkbypass.img;./qemu-img create nvm.img 5G;cd ../..
