import boto3
import logging
import os
from datetime import datetime
from PIL import Image, ExifTags

###################### Configuration and Setup ######################

# Logging config
logging.basicConfig(
    filename='backup.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AWS S3 user configuration
filepath_root = 'C:/YOUR/FILE/PATH'
storage_class = 'DEEP_ARCHIVE'
# AWS S3 bucket configuration  
fallback_bucket_name = None  # Fallback if TF not available. Change if needed

try:
    # Try to get bucket name from terraform output
    result = subprocess.run(['terraform', 'output', '-raw', 'bucket_name'], 
                           capture_output=True, text=True, cwd='.')
    bucket_name = result.stdout.strip() if result.returncode == 0 else fallback_bucket_name
except:
    bucket_name = fallback_bucket_name
    
# File tracking configuration
successful_uploads = 'successful-uploads.log'
failed_uploads = 'failed-uploads.log'

# Statistics tracking
uploaded_count = 0
skipped_count = 0
failed_count = 0
uploaded_size = 0

######################## Helper Functions ########################
# Thanks stackoverflow!
def get_exif_datetime(file_path):
    """Gets when the photo was taken"""
    try:
        img = Image.open(file_path)
        exif = img._getexif()
        if not exif:
            return None
        for tag_id, value in exif.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            if tag == "DateTimeOriginal":
                return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None
    return None

import subprocess
import json

def get_video_creation_time(file_path):
    """Extract creation time from video file metadata"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        info = json.loads(result.stdout)
        

        # Check format tags
        tags = info.get('format', {}).get('tags', {})
        if 'creation_time' in tags:
            value = tags['creation_time']
            try:
                # Parse datetime, ignoring timezone suffixes (Z and +hhmm)
                return datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S")
            except Exception:
                pass
        
        # Check streams for creation_time
        for stream in info.get('streams', []):
            stream_tags = stream.get('tags', {})
            if 'creation_time' in stream_tags:
                value = stream_tags['creation_time']
                try:
                    return datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S")
                except Exception:
                    pass
        
        # Check for Apple QuickTime creationdate
        if 'com.apple.quicktime.creationdate' in tags:
            value = tags['com.apple.quicktime.creationdate']
            try:
                # Remove timezone for parsing
                dt_str = value.split('+')[0]
                return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
            except Exception:
                pass
    except Exception:
        return None
    return None

def format_bytes(bytes_val):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"


############################ Main Execution ############################

# Initialize AWS S3 client and start backup
logging.info("Starting iOS backup to S3")
client = boto3.client("s3")

##################### S3 bucket scan #####################

logging.info("Checking S3 bucket for existing files")
current_files_in_bucket = 'currentfilesinbucket.log'
bucket_objects = set()

# Clear the bucket contents file
with open(current_files_in_bucket, 'w', encoding='utf-8') as f:
    pass  # Clear the file

paginator = client.get_paginator('list_objects_v2')
response_iterator = paginator.paginate(Bucket=bucket_name)
for page in response_iterator:
    if "Contents" in page:
        for obj in page["Contents"]:
            bucket_objects.add(obj["Key"])
            with open(current_files_in_bucket, 'a', encoding='utf-8') as f:
                f.write(f"{obj['Key']}\n")

logging.info(f"Found {len(bucket_objects)} existing files in S3 bucket")

#################### File preparation ####################


# Calculate total files and size for progress tracking
all_files = []
total_size = 0
for root, dirs, files in os.walk(filepath_root):
    for file in files:
        file_path = os.path.join(root, file)
        file_size = os.path.getsize(file_path)
        all_files.append((file_path, file, file_size))
        total_size += file_size

total_files = len(all_files)
logging.info(f"Found {total_files} files to process, total size: {format_bytes(total_size)}")
print(f"Found {total_files} files, total size: {format_bytes(total_size)}")

###################### Upload loop ######################

# Process each file | Track progress
fileCounter = 0

for file_path, file, file_size in all_files:
    # increment counter
    fileCounter += 1
    
    #Gets the date from photo metadata or uses modification time
    if file.lower().endswith((".jpg", ".jpeg", ".heic")):
        dt = get_exif_datetime(file_path) or datetime.fromtimestamp(os.path.getmtime(file_path))
    elif file.lower().endswith((".mp4", ".mov", ".m4v")):
        dt = get_video_creation_time(file_path)
        if not dt:
            print(f"Warning: No creation_time metadata found for {file_path}, using mtime.")
            dt = datetime.fromtimestamp(os.path.getmtime(file_path))
    else:
        dt = datetime.fromtimestamp(os.path.getmtime(file_path))


    s3_key = (
        f"ios/{dt.year}/"
        f"{dt.month:02d}/"
        f"{dt.strftime('%Y-%m-%d_%H-%M-%S')}_{file}"
    )
# print(f"Debug: {s3_key}")
    if s3_key in bucket_objects:
        skipped_count += 1
        print(f"{file_path} already in bucket! Will be skipped.")
        logging.info(f"Skipping duplicate file: {file_path}")
        continue
    else:
        print(f"[{fileCounter}/{total_files}] Uploading {s3_key} ({format_bytes(file_size)}) — Total size: {format_bytes(total_size)}")
        # TODO: ad retry logic when S3 fails
        try:
            client.upload_file(
                Filename=file_path,
                Bucket=bucket_name,
                Key=s3_key,
                ExtraArgs={'StorageClass': storage_class}
            )
            bucket_objects.add(s3_key)
            uploaded_count += 1
            uploaded_size += file_size
            logging.info(f'{file_path} uploaded.')
            print(f'{file_path} uploaded')
            with open(successful_uploads, 'a', encoding='utf-8') as f:
                f.write(f"{s3_key}\n")
        except Exception as e:
            failed_count += 1
            logging.error(f"Error uploading {file_path}: {e}")
            with open(failed_uploads, 'a', encoding='utf-8') as f:
                f.write(f"Error uploading {file_path} | {e}\n")

##################### Final results #####################

if uploaded_count == 0:
    print("Files not uploaded! Zero files to upload.")

if failed_count > 0:
    print(f"Total files failed: {failed_count}")


# Log final statistics
logging.info(f"Backup completed - Uploaded: {uploaded_count} ({format_bytes(uploaded_size)}), Skipped: {skipped_count}, Failed: {failed_count}")

# Print final summary
print(f"Total files uploaded: {uploaded_count}. Size of backed up files: {format_bytes(uploaded_size)}.")
print(f"Total files skipped (already in bucket): {skipped_count}")
print(f"Success log: {successful_uploads}")