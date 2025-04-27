#!/bin/bash

# Install gdown if not already installed
if ! command -v gdown &> /dev/null; then
    echo "Installing gdown..."
    pip install gdown
fi

output_dir="kernel_files"

# Create output directory
mkdir -p ${output_dir}

# Function to download a bzImage file using just the ID
download_kernel_files() {
    local version=$1
    local file_id=$2
    local vmlinux_id=$3

    echo "Downloading bzImage for kernel version ${version}..."
    gdown --id "$file_id"
    gdown --id "$vmlinux_id"

    if [ $? -eq 0 ]; then
        echo "Successfully downloaded"
    else
        echo "Failed to download bzImage for kernel version ${version}"
    fi
}

# Download each bzImage file
echo "=== Downloading bzImage files ==="
cd ${output_dir}
download_kernel_files "6.1.18" "14HNA5Gi3wfO7Icvvj9Kij2QYXyN1KnBP" "1flBgNfqaIGoPxCF9-HlLIYMrLzw-qXO8"
download_kernel_files "6.1.31" "18_i5Cr2Y56IhWUMfTpdaNF0miOlc4Rf_" "1bpf4PeS6Ci9KS8EZEMDwB_Fh7Rf3i_D7"
download_kernel_files "6.1.34" "1-R2tu3xnq8dZWGGVng6byAWcTAxILmgL" "1QxkS1a4Btxx00v95Md_pG1pdS6SBgMmW"
download_kernel_files "6.1.35" "1CATotVC_f5l68pHheWznfAJJ0-2Bg2EF" "1N7VLwHFSC8AAeOvnDjfDKhyEyjiD6G4r"
download_kernel_files "6.1.61" "1eFC3oGKQ-V6_b-XRGj9lrk7tUmhWlrGS" "1mC9hK4By6KfX4pVOP0532EmR4K2KCsub"
download_kernel_files "6.1.62" "1E0ZRAB2aPMEXj-SrmRG2sr8hiZHkiqJZ" "1l_aa5xe207Z_wbuOQn2eAdcr2dzc3lYQ"
download_kernel_files "6.1.66" "1aLKrm13kPr7eNAuWx8L7V2S_DzqKIwPb" "1Qh00LJOnQeItod9nUD_VoDFlqc8Gzi7i"
download_kernel_files "6.1.77" "1kN0nAEmlHVY2TC_x3ttfmo0o3iHGZSrw" "1i6dOpZb_a6YbwYw4nPTnDesR3voMcPy7"
download_kernel_files "6.1.84" "1MkWlkhjic-fRszYZnnrYll8r9zSHIgRn" "1H0jbnixkk-ffrKOnylCUY9PYRZJg3Qhb"
download_kernel_files "6.1.86" "1_SGRaSjQi0Q7rYypx_b8tDtuaQCxRmnl" "1ALYuxibg_nBRRNxA_aYQazJh7re08tqd"
download_kernel_files "6.1.0" "1a7aO4cTOibOySFlBS8zDnjszScO7rmV7" "134sQi4Ga4TFiMxCDuFnA_3IknSySdwfS"
download_kernel_files "5.10.222" "1n6UHSUfP2f1VZ3gcMZc9b3GEHmunOzDF" "1AAp6GArLXi_8VgInRF5BtDqPbgq8GhXF"
download_kernel_files "5.17.4" "1uRRK1ppPJf93U20tugymdCuyglZqyxJ3" "1oZW17z2zFp2h269RySTV0ch2nno2mt4-"

echo "All downloads complete."
