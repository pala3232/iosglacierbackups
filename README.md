# iOS Backup to S3 Glacier Deep Archive

Cloud photo storage gets expensive fast when you have thousands of iPhone photos. This script automates backups to AWS S3 Glacier Deep Archive for a fraction of the cost of traditional cloud storage services.

## What it does

- Scans your iOS backup folder for photos/videos (JPEG, HEIC, MP4, MOV)
- Extracts dates from EXIF data so everything gets organized properly
- Skips files that are already uploaded (no duplicates)
- Uploads everything to S3 with a clean folder structure like `ios/2025/02/2025-02-04_photo.jpg`
- Keeps detailed logs so you know what's happening behind

The Trick: pulling EXIF data from photos and using ffprobe for video metadata, so files get organized by when they were actually taken, not when you uploaded them.

## Setup

**Important:** Make sure your photos are transferred using a method that preserves EXIF metadata (e.g.):
- AirDrop
- Photos app export ("Export Unmodified Original")  
- iTunes backup extraction
- Direct cable/file copy

You'll also need:
- Python 3.7+
- AWS CLI configured
- FFmpeg installed
- Terraform (optional but recommended)

### Quick setup for Linux users

If you're on Ubuntu/Debian, there's a setup script that installs dependencies (including FFmpeg), and creates the S3 Bucket:

```bash
cd backup
chmod +x setup_linux.sh
./setup_linux.sh
```

If you proceed this way, then you can skip Step 3, 4 and 5.

### Manual setup

1. **Set up AWS credentials:**
```bash
aws configure
```

2. **Clone this repo:**
```bash
git clone https://github.com/pala3232/iosglacierbackups.git
cd iosglacierbackups
```

3. **Install FFmpeg:**

Windows: `choco install ffmpeg` or download from ffmpeg.org
macOS: `brew install ffmpeg`
Linux: `sudo apt install ffmpeg`

4. **Install Python dependencies:**
```bash
pip install -r backup/requirements.txt
```

5. **Create S3 bucket:**
```bash
cd terraform
terraform init
terraform apply
cd ../backup
```

6. **Edit the config:**
Open `backup/upload.py` and change these:

```python
# Point this to your photos folder
filepath_root = 'C:/Users/YourName/Pictures/iOS Photos'

# If you didn't use terraform, set a bucket name
fallback_bucket_name = 'your-backup-bucket-name'
```

## Running it

```bash
cd backup
python upload.py
```

It'll scan your photos, check what's already in S3, and upload the new stuff. Progress gets printed to console and logged to files.

You get these log files:
- `successful-uploads.log` - successfully uploaded files
- `failed-uploads.log` - upload failures with error details
- `backup.log` - detailed execution log
- `currentfilesinbucket.log` - existing S3 bucket contents

## How files get organized

Everything goes into a clean structure:
```
ios/
  2025/
    01/
      2025-01-15_14-30-22_IMG_001.jpg
      2025-01-15_14-31-45_VID_002.mp4
    02/
  2026/
```

## Storage costs

I use Glacier Deep Archive because it's EXTREMELY cost-effective - about $0.00099/GB/month. That's around $1/month for 1TB.

The tradeoff is retrieval takes 12+ hours, but for long-term photo backup that's fine. If you need faster access, change `storage_class` to `GLACIER` or `STANDARD_IA`. This will bring higher retrieval-storage costs but you can have faster access.

## Troubleshooting

**FFprobe not found:** Install FFmpeg and make sure it's in your PATH. Test with `ffprobe -version`

**AWS errors:** Run `aws configure` or check your environment variables

**Terraform issues:** Make sure you're running from the backup directory, or just set `fallback_bucket_name` manually

**Permission errors:** Your AWS user needs S3 access. Here's the basic policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-backup-bucket",
                "arn:aws:s3:::your-backup-bucket/*"
            ]
        }
    ]
}
```

## Technical details

- Uses boto3 for AWS access
- PIL/Pillow for EXIF data
- FFprobe for video metadata
- Terraform for infrastructure
- Automatic multipart uploads for big files

The script is smart about duplicate detection - it lists everything already in your bucket first, then only uploads new files. So you can run it multiple times safely.

## Getting your photos back

To retrieve photos from Glacier Deep Archive:
1. Initiate restore via AWS Console: "Restore from Glacier Deep Archive"
2. Wait 12+ hours for restoration
3. Download files when ready

Cost: ~$0.02/GB for retrieval requests.

## Performance

- Upload speed depends on your internet connection
- Handles files of any size via automatic multipart upload
- Metadata extraction adds minimal overhead (~1-2 seconds per 1000 files)

## What it doesn't do

- No direct iPhone integration (files must be on computer first)
- No automatic backup scheduling (run manually or via cron)
- No file compression (uploads original files)