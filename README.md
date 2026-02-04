# iOS Backup to S3

Python script that backs up photos and videos to AWS S3 with automatic metadata extraction and organization by date.

## What it does

- Scans your iOS photo/video folder 
- Extracts creation dates from EXIF data (photos) and metadata (videos)
- Organizes files by year/month in S3
- Skips duplicates
- Uses S3 Deep Archive for cost savings
- Handles multipart uploads automatically for large files (upload_file())

## Setup

### Quick setup (recommended)
Use the automated setup scripts:

**Debian/Ubuntu:**
```bash
chmod +x setup_linux.sh
./setup_linux.sh
```
Don't forget to add AWS credentials/Install Python/Terraform!

### Manual setup

#### Prerequisites 
- Python 3.7+
- AWS CLI configured with credentials
- FFmpeg/ffprobe (install separately - not via pip)
- Terraform (optional, for bucket creation)

#### Install dependencies
```bash
pip install -r requirements.txt
```

#### Install FFmpeg
**Linux:** `sudo apt install ffmpeg` (Ubuntu) or `sudo yum install ffmpeg` (CentOS)  
**Mac:** `brew install ffmpeg`  
**Windows:** `choco install ffmpeg` or download from ffmpeg.org

### Configure
1. Update `filepath_root` in upload.py to point to your photo folder
2. Either:
   - Use Terraform to create bucket (recommended), OR
   - Set `fallback_bucket_name` in the script to your bucket name

### Using with Terraform (recommended)
```bash
cd terraform/
terraform init
terraform apply
cd ../backup/
python upload.py
```

### Manual setup
If you don't want to use Terraform, just set the bucket name in upload.py:
```python
fallback_bucket_name = 'your-bucket-name-here'  
```
Note: Storage Class can also be set up with the storage_class variable. Default value is 'DEEP_ARCHIVE'.
## File organization in S3
```
ios/
  2023/
    01/
      2023-01-15_14-30-45_IMG_1234.jpg
      2023-01-15_16-22-10_VID_5678.mp4
  2024/
    12/
      2024-12-25_10-15-30_christmas.heic
```

## Notes
- Uses Deep Archive storage class (cheap but slow retrieval)
- Creates log files for tracking uploads/failures  
- Handles timezone info in video metadata
- Falls back to file modification time if no metadata found

## Logs
- `backup.log` - Main application log
- `successful-uploads.log` - List of uploaded files
- `failed-uploads.log` - Failed upload attempts

## Todo
- Add retry logic for S3 failures
- Progress bar for large uploads
- Email notifications when done