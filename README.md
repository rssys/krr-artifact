# KRR: Efficient and Scalable Kernel Record Replay

KRR is a kernel record replay tool supporting multi-core, it can record the guest kernel execution in KVM(hardware-assist virtualization) and replay it exactly in TCG(full emulation).

## Hardware Requirements
Intel with at least 32 cores and 64GB memory, we recommend `c6420` on [Cloudlab](https://docs.cloudlab.us/hardware.html#(part._hardware)) which is used in the experiments.

## Guest Kernel
We use our pre-built kernel image for both native and KRR's kernel, the native is based on this [source code version](https://github.com/tianrenz2/linux-6.1.0/tree/native) which is an unmodified 6.1.0 version except some extra modules used by DPDK. [Here](https://github.com/tianrenz2/linux-6.1.0/tree/smp-rr) is the KRR's kernel source code version.

## Environment
KRR's hypervisor is built upon Linux 5.17.5, and Ubuntu 22.04 is assumed to be used.

## Getting Started
1. Clone the repo, since this will download some large files, make sure it's executed on a disk with more than 100G space (we used the `sdb` on the recommended machine):
```
git clone https://github.com/tianrenz2/krr-artifact.git
```

2. Go to the project directory, prepare environment and tools:
```
make build
```
This command will download a few things for later experiment:
* `kernel-rr-linux`: KRR's host kernel code
* `qemu-tcg-kvm`: KRR's QEMU's code
* `bzImageNative`: Native kernel image for experiments
* `bzImageRR`: KRR kernel image
* `vmlinuxRR`: vmlinux for KRR kernel image
* `rootfs-bypass.qcow2`: rootfs disk for RocksDB experiment
* `rootfs-redis.qcow2`: rootfs disk for DPDK experiment
* `rootfs-kbuild.qcow2`: rootfs disk for kernel build experiment

If all goes well, you should see the message:
```
Setup finished, please reboot your machine to launch KRR kernel
```
Then reboot the machine to launch the KRR host kernel, its version should be `5.17.5+`

## Use KRR's record replay
[Here](tutorial/README.md) is a quick tutorial to use KRR's basic record-replay funtionality.

## Run Experiments
### Run RocksDB Benchmarks
***Key results: Figure 3, Figure 5***

1. Run benchmark RocksDB [estimated human time: < 1min, machine time: 3 ~ 3.5h]:
```
make run/rocksdb schemes=baseline,kernel_rr,whole_system_rr
```
Note: the `baseline` is the mode without record, `kernel_rr` is KRR record and `whole_system_rr` is the VM-RR record. The whole_system_rr takes the most of the time.

After test is succesfully finished, the graph is generated as `graph/rocksdb-throughput.pdf`.

2. Run benchmark RocksDB SPDK benchmarks [estimated human time: < 1min, machine time 1.5 ~ 2h]:
```
make run/rocksdb_spdk
```
After test is succesfully finished, the graph is generated as `graph/spdk-study.pdf`.

### Run Kernel build Benchmarks
***Key results: Figure 4***

Estimated human time: < 1min, machine time: 7 ~ 8 hours, the whole_system_rr solely takes 5+ hours.

```
make run/kernel_build schemes=baseline,kernel_rr,whole_system_rr
```
After test is succesfully finished, the graph is generated as `graph/kernel-compile.pdf`.

### Run DPDK Benchmarks
***Key results: Figure 6, Figure 7***

Estimated human time: 30 ~ 45 minutes, machine time: 2 ~ 2.5 hour (including both Redis and Nginx tests)

#### Hardware Requirement:
Two machines are used, server and client, recommend to set up two `c6420` machines.

#### Setup
Two servers are connected via a 1Gbps control link (Dell D3048 switches) and a 10Gbps experimental link (Dell S5048 switches). The server machine runs the testing vm with the dpdk app server and client machine runs the client. On the server machine, the 10Gbps NIC is passthrough to the VM, and it's ip is configured as `10.10.1.1`(hardcoded in the VM disk image yet), this is also the default ip when configuring with the [recommended machines](#hardware-requirement).

On server machine, Create the vfio device for the passthrough NIC:

List the interfaces, choose the interface for passthrough, it needs to be the one that connects the client machine:
```
lspci -nn | grep -i ethernet
18:00.0 Ethernet controller [0200]: Intel Corporation Ethernet Controller X710 for 10GbE SFP+ [8086:1572] (rev 02)
18:00.1 Ethernet controller [0200]: Intel Corporation Ethernet Controller X710 for 10GbE SFP+ [8086:1572] (rev 02)
lo:
```
For example, if choose `18:00.1`, then execute following:
```
echo "0000:18:00.1" > /sys/bus/pci/devices/0000\:18\:00.1/driver/unbind
modprobe vfio-pci
echo "8086 1572" > /sys/bus/pci/drivers/vfio-pci/new_id
```

#### Prepare server
If you already executed `make build` on the server host, then skip this step.

#### Prepare client environment
On the client machine, clone this repo and execute:
```
make build/client
```

#### Redis benchmark
On server machine, run the server:
```
make run/redis_server
```

On client machine, execute:
```
make run/redis_client host_ip=<the server host ip> vm_ip=10.10.1.1
```

After test is succesfully finished, the raw data is under `redis-data/` and graph is `garph/redis_dpdk_performance.pdf` on the client machine.

#### Nginx benchmark
On server machine, run the server:
```
make run/nginx_server
```

On client machine, execute:
```
make run/nginx_client host_ip=<the server host ip> vm_ip=10.10.1.1
```

After test is succesfully finished, the raw data is under `nginx-data/` and graph is `garph/nginx-dpdk-<file size>.pdf` on the client machine.


### Bug Reproduction
***Key results: Table 1***

Eestimated human time: 1h, machine time 3h ~ 4h

This section is about the bug reproduction experiment with KRR.

1. First, go to `kernel-rr-linux/`, make sure you are on the KRR's branch, if not, checkout to it and recompile:
```
cd kernel-rr-linux/
git checkout rr-para

# re-compile script
sh replace.sh 
```

Reload the KRR KVM modules with the following options:
```
rmmod kvm_intel
rmmod kvm
insmod arch/x86/kvm/kvm.ko rr_disable_avx=1
insmod arch/x86/kvm/kvm-intel.ko rr_trap_rdtsc=1
```
`rr_disable_avx`: Required, the testing kernel configs from syzbot have enabled some advanced features, such as aesni, that would use the avx instruction in kernel mode, KRR's replay currently has not supported the avx emulation, this option hides the avx from it.

`rr_trap_rdtsc`: Recommended, it makes RDTSC instruction in trap mode, helping reduce the rdtsc event number and save the KRR's logging space. ***Does not affect the reproducing results***

2. Download kernel images and disk image for the bug reproduction:
```
bash download_kernels.sh
```
This will download the kernel images listed in paper's table 1 into `kernel_files` directory, each file is named as `bzImage-<kernel version>`, please use corresponding kernel images based on the table to run the bug scripts.

3. Launch the VM:
For each bug, use the following QEMU command for recording, for bug #5, change the `-smp 1` to `-smp 2`:
```
../build/qemu-system-x86_64 -smp 1 -kernel <bzImage file> -accel kvm -cpu host -no-hpet -m 2G -append  "root=/dev/sda rw init=/lib/systemd/systemd tsc=reliable console=ttyS0 mce=off" -hda <disk image file> -object memory-backend-file,size=4096M,share,mem-path=/dev/shm/ivshmem,id=hostmem -device ivshmem-plain,memdev=hostmem -D rec.log -nographic -checkpoint-interval 0
```
After getting into the guest, login the `root` with password `abc123`.

4. Run the script:
In the guest's root directory, there are binary files named with `test-<hash>`, each one reproduces a bug, refer the table blow to get the bug's file:

| Bug No. | File Name |
|---------|-----------|
|   #1    | test-99bd |
|   #2    | test-e392 |
|   #3    | test-fb26 |
|   #4    | test-52a9 |
|   #5    | test-6c1b |
|   #6    | test-4b81 |
|   #7    | test-06c2 |
|   #8    | test-245c |
|   #9    | test-615d |
|   #10   | test-9d1d |
|   #11   | test-f0b0 |
|   #12   | test-94ed |

Start recording, `ctrl+A` and `C` to enter the QEMU monitor and execute:
```
rr_record test1
```

Execute the file to reproduce:
```
./test-<hash>
```

Once you see the crash message shows up, enter QEMU monitor and finish record by executing:
```
rr_end_record
```

5. Replay the bug:

For each bug use the following command, for bug #5, change the `-smp 1` to `-smp 2`:
```
../build/qemu-system-x86_64 -accel tcg -smp 1 -cpu Broadwell -no-hpet -m 2G -kernel <kernel image file> -append  "root=/dev/sda rw init=/lib/systemd/systemd tsc=reliable console=ttyS0 mce=off" -hda <disk image file> -device ivshmem-plain,memdev=hostmem -object memory-backend-file,size=4096M,share,mem-path=/dev/shm/ivshmem,id=hostmem -kernel-replay test1 -singlestep -D rec.log -monitor stdio
```
After launching, it would stay paused on QEMU monitor, type `cont` to start replaying.
