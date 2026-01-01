#!/usr/bin/env python3
"""
Test R2 connection and permissions
"""
import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')
R2_ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL')

print("Testing R2 Configuration:")
print(f"  Endpoint: {R2_ENDPOINT_URL}")
print(f"  Bucket: {R2_BUCKET_NAME}")
print(f"  Access Key ID: {R2_ACCESS_KEY_ID[:8]}..." if R2_ACCESS_KEY_ID else "  Access Key ID: NOT SET")
print(f"  Secret Key: {'SET' if R2_SECRET_ACCESS_KEY else 'NOT SET'}")
print()

# Create S3 client
s3 = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name='auto'
)

# Test 1: List buckets
print("Test 1: Listing buckets...")
try:
    response = s3.list_buckets()
    if 'Buckets' in response:
        print(f"✅ Success! Found {len(response['Buckets'])} bucket(s):")
        for bucket in response['Buckets']:
            print(f"   - {bucket['Name']}")
    else:
        print(f"⚠️  Got response but no buckets: {response}")
except ClientError as e:
    print(f"❌ Failed: {e}")
    print("   This might mean your credentials are wrong")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
print()

# Test 2: List objects in your bucket
print(f"Test 2: Listing objects in bucket '{R2_BUCKET_NAME}'...")
try:
    response = s3.list_objects_v2(Bucket=R2_BUCKET_NAME, MaxKeys=5)
    if 'Contents' in response:
        print(f"✅ Success! Found {len(response['Contents'])} object(s)")
        for obj in response['Contents']:
            print(f"   - {obj['Key']}")
    else:
        print(f"✅ Success! Bucket is empty (this is fine)")
except ClientError as e:
    print(f"❌ Failed: {e}")
    print("   Check:")
    print("   1. Bucket name is correct")
    print("   2. Token has 'Read' permission")
print()

# Test 3: Try to upload a small test file
print("Test 3: Uploading a test file...")
try:
    test_content = b"Test file from photography portfolio"
    s3.put_object(
        Bucket=R2_BUCKET_NAME,
        Key='test.txt',
        Body=test_content,
        ContentType='text/plain'
    )
    print("✅ Success! Upload works")
    print("   Cleaning up...")
    s3.delete_object(Bucket=R2_BUCKET_NAME, Key='test.txt')
    print("   ✅ Test file deleted")
except ClientError as e:
    print(f"❌ Failed: {e}")
    print("   Check:")
    print("   1. Token has 'Write' permission")
    print("   2. Bucket allows uploads")
print()

print("=" * 50)
print("If all tests passed, your R2 is configured correctly!")
print("If any failed, check the suggestions above.")
