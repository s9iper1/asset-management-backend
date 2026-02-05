"""
Credit system service for managing user credit transactions.

Handles credit deduction, addition, balance checks, and transaction logging
with atomic database operations.
"""
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from apps.authentication.models import User
from apps.properties.models import CreditTransaction


class InsufficientCreditsError(Exception):
    """Raised when user doesn't have enough credits for an operation"""
    pass


class CreditService:
    """Service for managing user credits"""

    @staticmethod
    def get_credit_cost(feature):
        """Get the credit cost for a feature from settings"""
        costs = {
            'ai_text': settings.CREDIT_COST_AI_TEXT,
            'ai_advisor': settings.CREDIT_COST_AI_ADVISOR,
            'valuo_api': settings.CREDIT_COST_VALUO_API,
            'realman_api': settings.CREDIT_COST_REALMAN_API,
        }
        return Decimal(str(costs.get(feature, 1)))

    @staticmethod
    def has_sufficient_credits(user, amount):
        """
        Check if user has enough credits

        Args:
            user: User object
            amount: Decimal amount to check

        Returns:
            bool: True if user has sufficient credits
        """
        return user.credit_balance >= Decimal(amount)

    @staticmethod
    @transaction.atomic
    def deduct_credits(user, amount, feature, description='', metadata=None):
        """
        Deduct credits from user account (BEFORE performing paid action)

        CRITICAL: This must be called BEFORE the paid action is performed.
       If the action fails, call refund_credits() to return the credits.

        Args:
            user: User object
            amount: Decimal amount to deduct
            feature: Feature name (ai_text, ai_advisor, valuo_api, realman_api)
            description: Transaction description
            metadata: Additional JSON metadata

        Returns:
            tuple: (new_balance, transaction_id)

        Raises:
            InsufficientCreditsError: If user lacks credits
        """
        amount = Decimal(str(amount))

        # Lock user row for update to prevent race conditions
        user = User.objects.select_for_update().get(pk=user.pk)

        if user.credit_balance < amount:
            raise InsufficientCreditsError(
                f"Required: {amount}, Available: {user.credit_balance}"
            )

        balance_before = user.credit_balance
        user.credit_balance -= amount
        balance_after = user.credit_balance
        user.save(update_fields=['credit_balance'])

        # Log transaction
        txn = CreditTransaction.objects.create(
            user=user,
            transaction_type='deduction',
            feature=feature,
            amount=-amount,  # Negative for deductions
            balance_before=balance_before,
            balance_after=balance_after,
            description=description or f"{feature} usage",
            metadata=metadata or {}
        )

        return balance_after, txn.id

    @staticmethod
    @transaction.atomic
    def refund_credits(user, amount, original_feature, description=''):
        """
        Refund credits (e.g., when API call fails after deduction)

        Args:
            user: User object
            amount: Decimal amount to refund
            original_feature: Original feature that was charged
            description: Refund reason

        Returns:
            Decimal: new_balance
        """
        amount = Decimal(str(amount))

        user = User.objects.select_for_update().get(pk=user.pk)

        balance_before = user.credit_balance
        user.credit_balance += amount
        balance_after = user.credit_balance
        user.save(update_fields=['credit_balance'])

        CreditTransaction.objects.create(
            user=user,
            transaction_type='refund',
            feature=original_feature,
            amount=amount,  # Positive for refunds
            balance_before=balance_before,
            balance_after=balance_after,
            description=description or f"Refund for {original_feature}",
            metadata={'refund_reason': description}
        )

        return balance_after

    @staticmethod
    @transaction.atomic
    def add_credits(user, amount, transaction_type='purchase', description='', metadata=None):
        """
        Add credits to user account (purchase, bonus, etc.)

        Args:
            user: User object
            amount: Decimal amount to add
            transaction_type: 'purchase', 'bonus', etc.
            description: Transaction description
            metadata: Additional JSON metadata (e.g., payment_id)

        Returns:
            Decimal: new_balance
        """
        amount = Decimal(str(amount))

        user = User.objects.select_for_update().get(pk=user.pk)

        balance_before = user.credit_balance
        user.credit_balance += amount
        balance_after = user.credit_balance
        user.save(update_fields=['credit_balance'])

        CreditTransaction.objects.create(
            user=user,
            transaction_type=transaction_type,
            feature='',
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description or f"Credit {transaction_type}",
            metadata=metadata or {}
        )

        return balance_after

    @staticmethod
    def get_transaction_history(user, limit=20, offset=0):
        """
        Get user's credit transaction history

        Args:
            user: User object
            limit: Number of transactions to return
            offset: Offset for pagination

        Returns:
            QuerySet: Credit transactions
        """
        return CreditTransaction.objects.filter(
            user=user
        ).order_by('-created_at')[offset:offset + limit]
