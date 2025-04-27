# KRR Record Performance

## Download disk images
Execute:
```
bash scripts/download_disks.sh
```
This will download:
* `rootfs-bypass.qcow2`: rootfs disk for RocksDB experiment
* `rootfs-redis.qcow2&img`: rootfs disk for DPDK experiment
* `rootfs-kbuild.qcow2`: rootfs disk for kernel build experiment
* `qemu-tcg-kvm/build/nkbypass.img&nvm.img`: data disks for benchmarks

## Run RocksDB Benchmarks
***Key results: Figure 3, Figure 5***

1. Run benchmark RocksDB [estimated human time: < 1min, machine time: 3 ~ 3.5h]:
```
make run/rocksdb schemes=baseline,kernel_rr,whole_system_rr
```
Note: the `baseline` is the mode without record, `kernel_rr` is KRR record and `whole_system_rr` is the VM-RR record. The whole_system_rr takes most of the time.

After the test is successfully finished, the graph is generated as `graph/rocksdb-throughput.pdf`.

2. Run benchmark RocksDB SPDK benchmarks [estimated human time: < 1min, machine time 1.5 ~ 2h]:
```
make run/rocksdb_spdk
```
After the test is successfully finished, the graph is generated as `graph/spdk-study.pdf`.

## Run Kernel build Benchmarks
***Key results: Figure 4***

Estimated human time: < 1min, machine time: 7 ~ 8 hours, the whole_system_rr solely takes 5+ hours.

```
make run/kernel_build schemes=baseline,kernel_rr,whole_system_rr
```
After the test is successfully finished, the graph is generated as `graph/kernel-compile.pdf`.

## Run DPDK Benchmarks
***Key results: Figure 6, Figure 7***

Estimated human time: 30 ~ 45 minutes, machine time: 2 ~ 2.5 hours (including both Redis and Nginx tests)

### Hardware Requirement:
Two machines are used, server and client, and we recommend using two `c6420` machines on CloudLab.

### Setup
Two servers are connected via a 1Gbps control link (Dell D3048 switches) and a 10Gbps experimental link (Dell S5048 switches). The server machine runs the testing VM with the DPDK app server, and the client machine runs the client. On the server machine, the 10Gbps NIC is passthrough to the VM, and it's ip is configured as `10.10.1.1`(hardcoded in the VM disk image yet), this is also the default IP when configuring with the [recommended machines](#hardware-requirement).

On the server machine, create the vfio device for the passthrough NIC:

List the interfaces:
```
lspci -nn | grep -i ethernet
18:00.0 Ethernet controller [0200]: Intel Corporation Ethernet Controller X710 for 10GbE SFP+ [8086:1572] (rev 02)
18:00.1 Ethernet controller [0200]: Intel Corporation Ethernet Controller X710 for 10GbE SFP+ [8086:1572] (rev 02)
lo:
```

In our experiment, we use the controller `18:00.1`, which is fixed on `c6420` machine, execute the following to make it usable for the VM:
```
echo "0000:18:00.1" > /sys/bus/pci/devices/0000\:18\:00.1/driver/unbind
modprobe vfio-pci
echo "8086 1572" > /sys/bus/pci/drivers/vfio-pci/new_id
```

### Prepare server
If you have already executed `make build` on the server host, then skip this step.

### Prepare the client environment
On the client machine, clone this repo and execute:
```
make build/client
```

### Redis benchmark
On the server machine, run the server:
```
make run/redis_server
```

On the client machine, execute:
```
make run/redis_client host_ip=<the server host ip> vm_ip=10.10.1.1
```

After the test is successfully finished, the raw data is under `redis-data/` and the graph is `graph/redis_dpdk_performance.pdf` on the client machine.

### Nginx benchmark
On the server machine, run the server:
```
make run/nginx_server
```

On the client machine, execute:
```
make run/nginx_client host_ip=<the server host ip> vm_ip=10.10.1.1
```

After the test is successfully finished, the raw data is under `nginx-data/` and the graph is `graph/nginx-dpdk-<file size>.pdf` on the client machine.

## Possible Errors Seen in Experiments
1. The error below could be ignored:
```
Standard Error:
42	../sysdeps/unix/sysv/linux/ppoll.c: No such file or directory.
```
