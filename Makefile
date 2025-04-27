
CURRENT_DIR := $(shell pwd)
schemes := baseline,kernel_rr,whole_system_rr
TEST_DATA = qemu-tcg-kvm/kernel_rr/test_data

$(info CURRENT_DIR = $(CURRENT_DIR))

test_data:
	mkdir -p $(TEST_DATA)

.PHONY: all
all: build

# Build target - executes the setup script
.PHONY: build
build:
	bash scripts/setup.sh

build/client:
	bash scripts/setup_client.sh

run/kernel_build: test_data
	bash scripts/kernel_benchmark.sh $(CURRENT_DIR) kernel_build $(schemes)

run/rocksdb: test_data
	bash scripts/rocksdb_benchmark.sh $(CURRENT_DIR) rocksdb $(schemes)

run/rocksdb_spdk: test_data
	bash scripts/rocksdb_benchmark.sh $(CURRENT_DIR)  rocksdb-spdk $(schemes)

run/redis_server:
	bash scripts/redis_benchmark.sh $(CURRENT_DIR) redis

run/redis_client:
	bash scripts/redis_benchmark_client.sh $(CURRENT_DIR) $(host_ip) $(vm_ip)

run/nginx_server:
	bash scripts/nginx_benchmark.sh $(CURRENT_DIR) nginx

run/nginx_client:
	bash scripts/nginx_benchmark_client.sh $(CURRENT_DIR) $(host_ip) $(vm_ip)


# Clean target (optional)
.PHONY: clean
clean:
	# Add commands to clean build artifacts
	@echo "Cleaning up..."
