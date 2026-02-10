import stripe
import os
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Initialize Stripe with API key from environment
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")


class StripePaymentProcessor:
    """Handle Stripe payment processing for GenAI API calls"""
    
    def __init__(self):
        """Initialize Stripe payment processor"""
        if not stripe.api_key:
            raise ValueError("STRIPE_SECRET_KEY environment variable not set")
    
    def create_payment_intent(
        self,
        amount_cents: int,
        currency: str = "usd",
        description: str = "GenAI API Call",
        customer_email: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a Stripe PaymentIntent for charging users
        
        Args:
            amount_cents: Amount in cents (e.g., 1000 = $10.00)
            currency: Currency code (default: usd)
            description: Payment description
            customer_email: Customer email address
            metadata: Additional metadata to track
            
        Returns:
            Payment intent details including client_secret
        """
        try:
            intent_params = {
                "amount": amount_cents,
                "currency": currency,
                "description": description,
                "metadata": metadata or {"app": "hello-genai"}
            }
            
            if customer_email:
                intent_params["receipt_email"] = customer_email
            
            intent = stripe.PaymentIntent.create(**intent_params)
            
            return {
                "success": True,
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "amount": intent.amount,
                "currency": intent.currency
            }
        except stripe.error.CardError as e:
            return {
                "success": False,
                "error": f"Card error: {e.user_message}"
            }
        except stripe.error.RateLimitError:
            return {
                "success": False,
                "error": "Rate limited. Please try again later."
            }
        except stripe.error.InvalidRequestError as e:
            return {
                "success": False,
                "error": f"Invalid request: {str(e)}"
            }
        except stripe.error.AuthenticationError:
            return {
                "success": False,
                "error": "Authentication failed with Stripe API"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def confirm_payment(self, payment_intent_id: str) -> Dict:
        """
        Confirm payment status
        
        Args:
            payment_intent_id: The Stripe PaymentIntent ID
            
        Returns:
            Payment confirmation status
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                "success": True,
                "payment_intent_id": intent.id,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency,
                "payment_complete": intent.status == "succeeded"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error confirming payment: {str(e)}"
            }
    
    def create_subscription(
        self,
        customer_email: str,
        price_id: str,
        return_url: str
    ) -> Dict:
        """
        Create a subscription for recurring payments
        
        Args:
            customer_email: Customer email
            price_id: Stripe Price ID for the plan
            return_url: URL to return after checkout
            
        Returns:
            Subscription session details
        """
        try:
            # Create or retrieve customer
            customers = stripe.Customer.list(email=customer_email, limit=1)
            
            if customers.data:
                customer = customers.data[0]
            else:
                customer = stripe.Customer.create(email=customer_email)
            
            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{"price": price_id}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"],
            )
            
            return {
                "success": True,
                "subscription_id": subscription.id,
                "customer_id": customer.id,
                "status": subscription.status
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating subscription: {str(e)}"
            }
    
    def calculate_api_cost(self, tokens_used: int, price_per_token: float = 0.0001) -> int:
        """
        Calculate API cost based on tokens used
        
        Args:
            tokens_used: Number of tokens processed
            price_per_token: Price per token (default: $0.0001)
            
        Returns:
            Cost in cents
        """
        cost_dollars = tokens_used * price_per_token
        cost_cents = int(cost_dollars * 100)
        return max(cost_cents, 50)  # Minimum 50 cents ($0.50)


def get_publishable_key() -> str:
    """Get Stripe publishable key for frontend"""
    return STRIPE_PUBLISHABLE_KEY or ""