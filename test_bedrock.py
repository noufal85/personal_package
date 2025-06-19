#!/usr/bin/env python3
"""
Minimal standalone test for AWS Bedrock API access
"""
import json
import boto3
from botocore.exceptions import ClientError

# Test configuration (same as in media_config.yaml)
REGION = "us-east-1"
MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"
MAX_TOKENS = 100
TEMPERATURE = 0.1

def test_bedrock_api():
    """Test basic Bedrock API access"""
    try:
        print(f"🔧 Testing Bedrock API...")
        print(f"   Region: {REGION}")
        print(f"   Model: {MODEL_ID}")
        
        # Initialize Bedrock client
        bedrock = boto3.client('bedrock-runtime', region_name=REGION)
        
        # Simple test prompt
        test_prompt = "Classify this filename: The.Dark.Knight.2008.1080p.BluRay.mkv"
        
        # Prepare request body
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "messages": [
                {
                    "role": "user",
                    "content": f"{test_prompt}\n\nRespond with only: MOVIE, TV, DOCUMENTARY, STANDUP, AUDIOBOOK, or OTHER"
                }
            ]
        }
        
        print("📡 Making API call...")
        
        # Call Bedrock
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(body),
            contentType='application/json',
            accept='application/json'
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        result = response_body['content'][0]['text'].strip()
        
        print(f"✅ SUCCESS! API Response: {result}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ AWS ClientError: {error_code}")
        print(f"   Message: {error_message}")
        
        if error_code == 'AccessDeniedException':
            print("   💡 Try: Check model access permissions in AWS Console")
        elif error_code == 'ValidationException':
            print("   💡 Try: Check model ID is correct for this region")
            
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🤖 AWS Bedrock API Test")
    print("=" * 40)
    
    # Check AWS credentials
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials:
            print(f"✅ AWS credentials found")
        else:
            print("❌ No AWS credentials found")
            exit(1)
    except Exception:
        print("❌ AWS credentials error")
        exit(1)
    
    # Test API
    success = test_bedrock_api()
    
    if success:
        print("\n🎉 Bedrock API is working correctly!")
    else:
        print("\n💥 Bedrock API test failed")
        print("   Consider using rule-based classification instead")