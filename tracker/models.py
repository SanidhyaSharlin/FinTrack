from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # The primary classification (Income/Expense)
    type = models.CharField(
        max_length=7, 
        choices=TRANSACTION_TYPES,
        help_text="Is this money coming in or going out?"
    )
    
    # Financial classification for detailed tracking
    category_type = models.CharField(
        max_length=10, 
        choices=[
            ('income', 'Income'),
            ('expense', 'Expense'),
            ('savings', 'Savings'),
            ('debt', 'Debt'),
        ],
        default='expense',
        help_text="Select whether this is money coming in, going out, saved, or owed."
    )
    
    # Specific category (e.g., Food, Salary, Rent)
    category = models.CharField(
        max_length=100,
        help_text="Enter a specific category (e.g., Food, Travel, Rent, Salary)."
    )
    date = models.DateField()
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.amount} ({self.date})"
