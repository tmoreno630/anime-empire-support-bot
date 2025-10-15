"""
Shopify Integration using Admin API
Handles order lookups, status checks, fulfillment tracking
"""

import requests
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import pytz

class ShopifyIntegration:
    def __init__(self, shop_domain: str, access_token: str):
        self.shop_domain = shop_domain.replace('https://', '').replace('http://', '')
        self.access_token = access_token
        self.base_url = f"https://{self.shop_domain}/admin/api/2024-01"

    def _make_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Optional[Dict]:
        """
        Make authenticated request to Shopify API
        """
        headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }

        url = f"{self.base_url}/{endpoint}"

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            else:
                return None

            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Shopify API error: {e}")
            return None

    def find_order_by_email(self, email: str, limit: int = 10) -> List[Dict]:
        """
        Find orders by customer email
        Returns list of order summaries
        """
        endpoint = f"orders.json?email={email}&limit={limit}&status=any"
        result = self._make_request(endpoint)

        if not result or 'orders' not in result:
            return []

        orders = []
        for order in result['orders']:
            orders.append(self._format_order_info(order))

        return orders

    def find_order_by_number(self, order_number: str) -> Optional[Dict]:
        """
        Find specific order by order number
        """
        endpoint = f"orders.json?name=%23{order_number}&status=any"
        result = self._make_request(endpoint)

        if not result or 'orders' not in result or len(result['orders']) == 0:
            return None

        return self._format_order_info(result['orders'][0])

    def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """
        Get order by Shopify order ID
        """
        endpoint = f"orders/{order_id}.json"
        result = self._make_request(endpoint)

        if not result or 'order' not in result:
            return None

        return self._format_order_info(result['order'])

    def _format_order_info(self, order: Dict) -> Dict:
        """
        Format order data into consistent structure
        """
        order_number = order.get('name', '').replace('#', '')
        created_at = order.get('created_at', '')

        # Calculate expected delivery dates
        order_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')) if created_at else datetime.now(pytz.UTC)
        expected_min = order_date + timedelta(days=10)
        expected_max = order_date + timedelta(days=14)

        # Get fulfillment status
        fulfillment_status = order.get('fulfillment_status') or 'unfulfilled'

        # Get tracking info from fulfillments
        tracking_info = []
        fulfillments = order.get('fulfillments', [])
        for fulfillment in fulfillments:
            if fulfillment.get('tracking_number'):
                tracking_info.append({
                    'number': fulfillment['tracking_number'],
                    'company': fulfillment.get('tracking_company', 'Unknown'),
                    'url': fulfillment.get('tracking_url', ''),
                    'status': fulfillment.get('shipment_status', 'in_transit')
                })

        # Get line items
        line_items = []
        for item in order.get('line_items', []):
            line_items.append({
                'name': item.get('name', ''),
                'quantity': item.get('quantity', 1),
                'price': item.get('price', '0.00')
            })

        return {
            'order_id': order.get('id'),
            'order_number': order_number,
            'created_at': created_at,
            'order_date': order_date.isoformat(),
            'expected_delivery_min': expected_min.isoformat(),
            'expected_delivery_max': expected_max.isoformat(),
            'fulfillment_status': fulfillment_status,
            'financial_status': order.get('financial_status', 'pending'),
            'total_price': order.get('total_price', '0.00'),
            'currency': order.get('currency', 'USD'),
            'customer_email': order.get('email', ''),
            'customer_name': f"{order.get('customer', {}).get('first_name', '')} {order.get('customer', {}).get('last_name', '')}".strip(),
            'shipping_address': order.get('shipping_address', {}),
            'tracking_info': tracking_info,
            'line_items': line_items,
            'note': order.get('note', ''),
            'tags': order.get('tags', '')
        }

    def update_shipping_address(self, order_id: str, new_address: Dict) -> bool:
        """
        Update shipping address for unfulfilled order
        """
        endpoint = f"orders/{order_id}.json"

        data = {
            'order': {
                'shipping_address': new_address
            }
        }

        result = self._make_request(endpoint, method='PUT', data=data)
        return result is not None

    def get_fulfillment_status(self, order_id: str) -> Optional[str]:
        """
        Get current fulfillment status
        """
        order = self.get_order_by_id(order_id)
        if order:
            return order.get('fulfillment_status', 'unfulfilled')
        return None

    def check_if_delivered(self, order_id: str) -> bool:
        """
        Check if order has been delivered based on tracking
        """
        order = self.get_order_by_id(order_id)
        if not order or not order.get('tracking_info'):
            return False

        for tracking in order['tracking_info']:
            if tracking.get('status') in ['delivered', 'out_for_delivery']:
                return True

        return False


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    shopify = ShopifyIntegration(
        shop_domain=os.getenv('SHOPIFY_DOMAIN'),
        access_token=os.getenv('SHOPIFY_ACCESS_TOKEN')
    )

    # Test connection
    print("Testing Shopify connection...")
    test_order = shopify._make_request('orders.json?limit=1')
    if test_order:
        print("✅ Shopify connection successful")
    else:
        print("❌ Shopify connection failed")
