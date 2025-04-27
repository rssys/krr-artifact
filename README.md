# KRR: Efficient and Scalable Kernel Record Replay

***KRR*** is a record-replay (RR) tool for the operating system kernel, designed to achieve low recording overhead. Unlike existing RR systems that capture entire VM or user-space execution, KRR focuses on the kernel boundary, recording only the inputs that cross into the kernel space. This new approach significantly reduces recording overhead while maintaining accurate and reliable replay.

For more details, please refer to our paper:
> KRR: Efficient and Scalable Kernel Record Replay
> Tianren Zhang, Sishuai Gong, Pedro Fonseca

## Features
Record:
* Supports KVM-accelerated VMs
* Records multi-core kernel execution

Replay:
* Replays the kernel using a modified QEMU emulator
* Support single-step debugging
* Supports reverse debugging

## Hardware Requirements
### Recommended
We recommend using machines from [Cloudlab](https://docs.cloudlab.us/hardware.html).
* `c6420` for [recording performance](#record-performance).
* `c220g5`/`sm110p` for [bug reproduction](#bug-reproduction). 

### Minimal
Any machines with support for Intel Performance Monitoring Unit and VT-d, 64GB memory and at least 200GB disk space should be sufficient.

## Software Requirements
### Host OS
KRR requires a Linux kernel with a modified KVM module. We provide a modified Linux kernel 5.17.5 ([here](https://github.com/tianrenz2/kernel-rr-linux/tree/rr-para)) in this repo. This setup also assumes you are running Ubuntu 22.04 on the host.

### Guest OS
The guest kernel must also include modifications to support efficient recording. This repo includes our modified guest kernel ([here](https://github.com/tianrenz2/linux-6.1.0/tree/smp-rr)), which is based on Linux kernel 6.1.0. For performance comparison, we also provide the unmodified kernel source as a baseline source code version.


## General Usage
### Clone the repo
Ensure you have at least 100GB of free disk space, as the scripts will download large files such as disk images.

Get the artifact repo:
```
git clone https://github.com/rssys/krr-artifact.git
```

### Install KKR
Go to the project directory, set up the environment with the following commands:
```
make build
```
This command will download and install the following things:
* `kernel-rr-linux`: KRR's host kernel code
* `qemu-tcg-kvm`: KRR's QEMU's code
* `bzImageNative`: Unmodified guest kernel image for experiments
* `bzImageRR`: KRR guest kernel image
* `vmlinuxRR`: vmlinux for KRR guest kernel image
* `rootfs-bug.qcow2`: rootfs disk for bug reproduction experiment (root password: `abc123`)

If all goes well, you should see the message:
```
Setup finished, please reboot your machine to launch KRR kernel
```
Then reboot the machine to launch KRR’s host kernel.

### Use KRR to record and replay
[Here](tutorial/README.md) is a quick tutorial on using KRR's basic record-replay functionality.

## Artifact evaluation guidance
The following instructions walk you through reproducing the key results from our paper.
Before proceeding, please make sure you have completed Step 1 and Step 2 in the General Usage section.

### Bug Reproduction
Follow the instruction [here](bug-repro.md).

### Record Performance
Follow the instruction [here](record-perf.md).
