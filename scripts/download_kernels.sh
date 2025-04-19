#!/bin/bash

# Install gdown if not already installed
if ! command -v gdown &> /dev/null; then
    echo "Installing gdown..."
    pip install gdown
fi

# Create output directory
mkdir -p kernel_files

# Function to download a kernel file using just the ID
download_kernel() {
    local version=$1
    local file_id=$2
    local output_file="kernel_files/bzImage-${version}"
    
    echo "Downloading kernel version ${version}..."
    gdown --id "$file_id" -O "$output_file"
    
    if [ $? -eq 0 ]; then
        echo "Successfully downloaded ${output_file}"
    else
        echo "Failed to download kernel version ${version}"
    fi
}

# Download each kernel file using just the ID
download_kernel "6.1.18" "14HNA5Gi3wfO7Icvvj9Kij2QYXyN1KnBP"
download_kernel "6.1.31" "18_i5Cr2Y56IhWUMfTpdaNF0miOlc4Rf_"
download_kernel "6.1.34" "1-R2tu3xnq8dZWGGVng6byAWcTAxILmgL"
download_kernel "6.1.35" "1CATotVC_f5l68pHheWznfAJJ0-2Bg2EF"
download_kernel "6.1.61" "1eFC3oGKQ-V6_b-XRGj9lrk7tUmhWlrGS"
download_kernel "6.1.62" "1E0ZRAB2aPMEXj-SrmRG2sr8hiZHkiqJZ"
download_kernel "6.1.66" "1aLKrm13kPr7eNAuWx8L7V2S_DzqKIwPb"
download_kernel "6.1.77" "1kN0nAEmlHVY2TC_x3ttfmo0o3iHGZSrw"
download_kernel "6.1.84" "1MkWlkhjic-fRszYZnnrYll8r9zSHIgRn"
download_kernel "6.1.86" "1_SGRaSjQi0Q7rYypx_b8tDtuaQCxRmnl"

echo "All downloads complete."
