import requests
import json
import time

def test_s3_operations(api_url, api_key):
    # Remove trailing slash if present
    api_url = api_url.rstrip('/')
    
    # Test file content
    test_data = {
        'key': 'test.txt',
        'operation': 'upload',
        'content_type': 'text/plain'
    }
    
    # Headers for API Gateway
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }
    
    print("\n=== Testing S3 Operations ===")
    
    # 1. Test Upload
    print("\n1. Testing Upload...")
    response = requests.post(f"{api_url}/signed-url", json=test_data, headers=headers)
    if response.status_code != 200:
        print(f"Upload URL generation failed: {response.text}")
        return
    
    upload_url = response.json().get('signed_url')
    print(f"Got signed URL for upload: {upload_url[:100]}...")
    
    # Upload content
    content = "Hello, this is a test file!"
    upload_response = requests.put(upload_url, data=content)
    print(f"Upload response status: {upload_response.status_code}")
    
    # Wait a moment for consistency
    time.sleep(2)
    
    # 2. Test Download
    print("\n2. Testing Download...")
    test_data['operation'] = 'download'
    response = requests.post(f"{api_url}/signed-url", json=test_data, headers=headers)
    if response.status_code != 200:
        print(f"Download URL generation failed: {response.text}")
        return
    
    download_url = response.json().get('signed_url')
    print(f"Got signed URL for download: {download_url[:100]}...")
    
    # Download content
    download_response = requests.get(download_url)
    print(f"Download response status: {download_response.status_code}")
    print(f"Downloaded content: {download_response.text}")
    
    # 3. Test Delete
    print("\n3. Testing Delete...")
    test_data['operation'] = 'delete'
    response = requests.post(f"{api_url}/signed-url", json=test_data, headers=headers)
    if response.status_code != 200:
        print(f"Delete URL generation failed: {response.text}")
        return
    
    delete_url = response.json().get('signed_url')
    print(f"Got signed URL for delete: {delete_url[:100]}...")
    
    # Delete file
    delete_response = requests.delete(delete_url)
    print(f"Delete response status: {delete_response.status_code}")
    
    # 4. Verify Delete
    print("\n4. Verifying Delete...")
    test_data['operation'] = 'download'
    response = requests.post(f"{api_url}/signed-url", json=test_data, headers=headers)
    download_url = response.json().get('signed_url')
    verify_response = requests.get(download_url)
    print(f"Verify delete status (should be 403 or 404): {verify_response.status_code}")

if __name__ == "__main__":
    # Get the API URL from Zappa output
    api_url = input("Please enter your API URL: ")
    api_key = input("Please enter your API key: ")
    test_s3_operations(api_url, api_key) 