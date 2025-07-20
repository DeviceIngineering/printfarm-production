#!/usr/bin/env python3
"""
Test script for images API endpoint.
"""
import requests
import json

def test_images_api():
    """Test the products API with images."""
    
    # API endpoint
    url = "http://localhost:8000/api/v1/products/"
    headers = {
        "Authorization": "Token 549ebaf641ffa608a26b79a21d72a296c99a02b7",
        "Content-Type": "application/json"
    }
    
    params = {
        "page_size": 10,
        "ordering": "-last_synced_at"
    }
    
    print("🔍 Testing products API with images...")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        products = data.get('results', [])
        
        print(f"✅ API Response successful!")
        print(f"📊 Total products: {data.get('count', 0)}")
        print(f"📦 Products in response: {len(products)}")
        
        # Analyze images
        products_with_images = [p for p in products if p.get('images') and len(p['images']) > 0]
        products_without_images = [p for p in products if not p.get('images') or len(p['images']) == 0]
        
        print(f"🖼️  Products with images: {len(products_with_images)}")
        print(f"📋 Products without images: {len(products_without_images)}")
        
        # Show some examples
        print("\n🖼️  Examples of products WITH images:")
        for i, product in enumerate(products_with_images[:5], 1):
            article = product.get('article', 'N/A')
            name = product.get('name', 'N/A')[:50]
            image_count = len(product.get('images', []))
            main_image = product.get('main_image')
            
            print(f"  {i}. {article}: {name}... ({image_count} images)")
            print(f"     Main image: {'✅ Yes' if main_image else '❌ No'}")
            if main_image:
                print(f"     URL: {main_image}")
        
        print("\n📋 Examples of products WITHOUT images:")
        for i, product in enumerate(products_without_images[:5], 1):
            article = product.get('article', 'N/A')
            name = product.get('name', 'N/A')[:50]
            
            print(f"  {i}. {article}: {name}...")
        
        # Test image accessibility
        if products_with_images:
            test_product = products_with_images[0]
            main_image_url = test_product.get('main_image')
            
            if main_image_url:
                print(f"\n🌐 Testing image accessibility:")
                print(f"   URL: {main_image_url}")
                
                try:
                    img_response = requests.head(main_image_url)
                    if img_response.status_code == 200:
                        print(f"   ✅ Image accessible (200 OK)")
                        print(f"   📏 Content-Type: {img_response.headers.get('Content-Type', 'unknown')}")
                    else:
                        print(f"   ❌ Image not accessible ({img_response.status_code})")
                except Exception as e:
                    print(f"   ❌ Error accessing image: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False

if __name__ == '__main__':
    test_images_api()