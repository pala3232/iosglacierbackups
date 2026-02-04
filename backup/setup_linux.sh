#!/bin/bash

# Setup script for Ubuntu/Debian - installs ffmpeg / dependencies / provisions S3 bucket

echo "Setting up iOS Backup environment..."
sudo apt-get update
sudo apt-get install -y ffmpeg
# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
# Provision S3 bucket with Terraform
echo "Provisioning S3 bucket..."
cd ../terraform/
terraform init
terraform apply -auto-approve
echo "Setup complete!"
echo "Now just run: python uptest2.py | Everything will be backed up!"