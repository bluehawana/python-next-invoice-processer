import boto3
import os
from botocore.exceptions import NoCredentialsError
from stripe_module import settings

def get_r2_client():
    """
    Returns a boto3 client for Cloudflare R2.
    """
    endpoint = os.getenv("R2_ENDPOINT_URL")
    key_id = os.getenv("R2_ACCESS_KEY_ID")
    secret = os.getenv("R2_SECRET_ACCESS_KEY")
    
    if not endpoint or not key_id or not secret or "YOUR_" in key_id:
        print("R2 credentials missing or incomplete in .env")
        return None
        
    try:
        s3 = boto3.client(
            service_name='s3',
            endpoint_url=endpoint,
            aws_access_key_id=key_id,
            aws_secret_access_key=secret,
            region_name='auto' # R2 uses 'auto'
        )
        return s3
    except Exception as e:
        print(f"Failed to create R2 client: {e}")
        return None

def upload_file_to_r2(file_path: str, object_name: str = None) -> str:
    """
    Uploads a file to R2 and returns the public (or signed) URL.
    Deletes the local file upon success.
    """
    s3 = get_r2_client()
    if not s3:
        return file_path # Fallback to local path

    bucket_name = os.getenv("R2_BUCKET_NAME", "invoice-archive")
    
    if object_name is None:
        object_name = os.path.basename(file_path)

    try:
        # Check if file already exists in R2
        try:
            s3.head_object(Bucket=bucket_name, Key=object_name)
            print(f"File {object_name} already exists in R2. Skipping upload.")
            if os.path.exists(file_path):
                 os.remove(file_path)
            return f"r2://{bucket_name}/{object_name}"
        except:
             # File does not exist, proceed with upload
             pass

        print(f"Uploading {object_name} to R2 bucket '{bucket_name}'...")
        s3.upload_file(file_path, bucket_name, object_name)
        
        # Verify upload (optional, but good for safety before delete)
        # s3.head_object(Bucket=bucket_name, Key=object_name)
        
        print(f"Upload successful. Deleting local file: {file_path}")
        os.remove(file_path)
        
        # Return a URL. 
        # If the bucket is public: f"https://pub-domain/{object_name}"
        # If private, we might need a presigned URL, but for now we'll return the object key
        # and let the frontend/backend request a signed URL when viewing.
        # Ideally, user sets up a custom domain.
        
        # For this implementation, we will return a special prefix so the frontend knows it's remote.
        return f"r2://{bucket_name}/{object_name}"
        
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return file_path
    except NoCredentialsError:
        print("Credentials not available")
        return file_path
    except Exception as e:
        print(f"Upload failed: {e}")
        return file_path

def generate_presigned_url(r2_uri: str):
    """
    Generates a temporary public URL for a private R2 object.
    Input: r2://bucket-name/object-key
    """
    if not r2_uri.startswith("r2://"):
        return r2_uri
        
    parts = r2_uri.replace("r2://", "").split("/", 1)
    if len(parts) != 2: return None
    bucket, key = parts
    
    s3 = get_r2_client()
    if not s3: return None
    
    try:
        url = s3.generate_presigned_url('get_object',
                                        Params={'Bucket': bucket,
                                                'Key': key},
                                        ExpiresIn=3600)
        return url
    except Exception as e:
        print(f"Failed to sign URL: {e}")
        return None
