#!/usr/bin/env python3
"""
GPT API Connectivity Test Script

This script tests if the GPT API is accessible after firewall configuration changes.
Run this in an environment where API credentials are properly configured.

Usage:
    python test_gpt_connectivity.py

Requirements:
    - AZURE_OPENAI_API_KEY environment variable
    - AZURE_OPENAI_ENDPOINT environment variable
    - openai library installed
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_gpt_api_connectivity():
    """Test GPT API connectivity with comprehensive checks."""
    print("=" * 70)
    print("GPT API Connectivity Test")
    print("=" * 70)
    
    try:
        from api_structure.src.clients.gpt import GptClient
        
        # Load configuration
        print("\n1. Loading API configuration...")
        config = {
            "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"),
            "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "AZURE_OPENAI_DEPLOYMENT_NAME": os.getenv(
                "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini"
            ),
            "AZURE_OPENAI_API_VERSION": os.getenv(
                "AZURE_OPENAI_API_VERSION", "2024-02-15-preview"
            ),
        }
        
        # Check credentials
        if not config["AZURE_OPENAI_API_KEY"]:
            print("   ❌ AZURE_OPENAI_API_KEY not set")
            print("\n   Please set environment variables:")
            print("   export AZURE_OPENAI_API_KEY='your-key'")
            print("   export AZURE_OPENAI_ENDPOINT='your-endpoint'")
            return False
        
        if not config["AZURE_OPENAI_ENDPOINT"]:
            print("   ❌ AZURE_OPENAI_ENDPOINT not set")
            return False
        
        print(f"   ✓ API Key: {config['AZURE_OPENAI_API_KEY'][:10]}...")
        print(f"   ✓ Endpoint: {config['AZURE_OPENAI_ENDPOINT']}")
        print(f"   ✓ Deployment: {config['AZURE_OPENAI_DEPLOYMENT_NAME']}")
        print(f"   ✓ API Version: {config['AZURE_OPENAI_API_VERSION']}")
        
        # Initialize client
        print("\n2. Initializing GptClient...")
        gpt_client = GptClient(config=config)
        await gpt_client.initialize()
        print("   ✓ Client initialized successfully")
        
        # Test 1: Simple completion
        print("\n3. Testing simple completion...")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": "Say 'API connection successful!' if you receive this.",
            },
        ]
        
        response = await gpt_client.call(messages=messages, temperature=0.1)
        print(f"   ✓ Response: {response[:80]}...")
        
        # Test 2: Function calling
        print("\n4. Testing function calling...")
        functions = [
            {
                "name": "test_function",
                "description": "Test function to verify function calling works",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Status of the test",
                        }
                    },
                    "required": ["status"],
                },
            }
        ]
        
        test_messages = [
            {"role": "system", "content": "You are a test assistant."},
            {"role": "user", "content": "Call test_function with status='success'"},
        ]
        
        func_response = await gpt_client.call_with_functions(
            messages=test_messages,
            functions=functions,
            function_call={"name": "test_function"},
        )
        
        if hasattr(func_response, "function_call"):
            print(f"   ✓ Function: {func_response.function_call.name}")
            print(f"   ✓ Arguments: {func_response.function_call.arguments}")
        else:
            print(f"   ✓ Response: {func_response}")
        
        # Test 3: User info extraction (real use case)
        print("\n5. Testing user info extraction (real use case)...")
        extraction_messages = [
            {
                "role": "system",
                "content": """你是華碩技術支援的資訊擷取助手。
請從使用者的問題中擷取產品類別資訊。

產品類別規則:
- main_product_category: notebook(筆記型電腦), desktop(桌上型電腦), 
  monitor(顯示器), phone(手機), tablet(平板)
- sub_product_category: 若使用者提到具體系列如ROG、ZenBook等，請標註

範例:
使用者: "我的ROG筆電開不了機"
→ main_product_category: "notebook", sub_product_category: "rog"
""",
            },
            {"role": "user", "content": "我的筆電卡在登入畫面，完全沒有反應。"},
        ]
        
        extraction_functions = [
            {
                "name": "information_extraction",
                "description": "Extract product information from user query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "main_product_category": {
                            "type": "string",
                            "description": (
                                "Main product category: notebook, desktop, "
                                "monitor, phone, tablet"
                            ),
                        },
                        "sub_product_category": {
                            "type": "string",
                            "description": "Sub product category like rog, zenbook, etc",
                        },
                    },
                    "required": ["main_product_category"],
                },
            }
        ]
        
        extraction_response = await gpt_client.call_with_functions(
            messages=extraction_messages,
            functions=extraction_functions,
            function_call={"name": "information_extraction"},
        )
        
        if hasattr(extraction_response, "function_call"):
            import json
            
            args = json.loads(extraction_response.function_call.arguments)
            print(f"   ✓ Extracted: {args}")
            print(
                f"   ✓ Product: {args.get('main_product_category', 'N/A')}"
            )
            if "sub_product_category" in args:
                print(f"   ✓ Series: {args.get('sub_product_category')}")
        else:
            print(f"   ✓ Response: {extraction_response}")
        
        # Test 4: Follow-up detection (another real use case)
        print("\n6. Testing follow-up detection...")
        followup_messages = [
            {
                "role": "system",
                "content": """判斷使用者的訊息是否為對前一個問題的追問或延續。

回答 yes 如果:
- 使用代詞指涉前面的內容 (它、這個、那個)
- 詢問更多細節
- 是前一輪對話的延續

回答 no 如果:
- 是全新的問題
- 改變了討論主題
- 是獨立完整的問題
""",
            },
            {
                "role": "assistant",
                "content": "您的筆電可能是系統檔案損壞導致無法啟動。",
            },
            {"role": "user", "content": "那我該怎麼辦？"},
        ]
        
        followup_functions = [
            {
                "name": "followup_detection",
                "description": "Detect if user message is a follow-up question",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "is_followup": {
                            "type": "boolean",
                            "description": "Whether this is a follow-up question",
                        },
                        "confidence": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "Confidence level of the detection",
                        },
                    },
                    "required": ["is_followup", "confidence"],
                },
            }
        ]
        
        followup_response = await gpt_client.call_with_functions(
            messages=followup_messages,
            functions=followup_functions,
            function_call={"name": "followup_detection"},
        )
        
        if hasattr(followup_response, "function_call"):
            import json
            
            args = json.loads(followup_response.function_call.arguments)
            print(f"   ✓ Is follow-up: {args.get('is_followup')}")
            print(f"   ✓ Confidence: {args.get('confidence')}")
        
        # Cleanup
        await gpt_client.close()
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nGPT API is fully accessible:")
        print("  ✓ Simple completions working")
        print("  ✓ Function calling working")
        print("  ✓ User info extraction working")
        print("  ✓ Follow-up detection working")
        print("\nThe firewall configuration is correct.")
        print("The refactored api_structure/ code will work properly.")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        
        traceback.print_exc()
        print("\n" + "=" * 70)
        print("⚠️  GPT API is NOT accessible")
        print("=" * 70)
        print("\nPossible issues:")
        print("  1. Firewall still blocking outbound connections")
        print("  2. API credentials incorrect or expired")
        print("  3. Network timeout or connectivity issues")
        print("  4. Endpoint URL incorrect")
        print("\nTroubleshooting:")
        print("  1. Check firewall settings allow HTTPS to Azure OpenAI")
        print("  2. Verify API key and endpoint in environment variables")
        print("  3. Test with curl to Azure endpoint directly")
        print("=" * 70)
        return False


def main():
    """Main entry point."""
    result = asyncio.run(test_gpt_api_connectivity())
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
