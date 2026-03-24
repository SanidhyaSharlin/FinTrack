import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.db.models import Sum
from .models import Transaction
from .forms import TransactionForm

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
        
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    all_transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    
    # Extract filters
    filter_category_type = request.GET.get('category_type')
    filter_start_date = request.GET.get('start_date')
    filter_end_date = request.GET.get('end_date')
    filter_category = request.GET.get('category')
    
    # Apply filters
    if filter_category_type:
        all_transactions = all_transactions.filter(category_type=filter_category_type)
    if filter_start_date:
        all_transactions = all_transactions.filter(date__gte=filter_start_date)
    if filter_end_date:
        all_transactions = all_transactions.filter(date__lte=filter_end_date)
    if filter_category:
        all_transactions = all_transactions.filter(category__icontains=filter_category)
    
    # Separate transactions by category_type (using filtered queryset)
    income_transactions = all_transactions.filter(category_type='income')
    expense_transactions = all_transactions.filter(category_type='expense')
    savings_transactions = all_transactions.filter(category_type='savings')
    debt_transactions = all_transactions.filter(category_type='debt')
    
    # Calculate totals based on filtered transactions
    totals = all_transactions.values('category_type').annotate(total=Sum('amount'))
    
    income = 0
    expense = 0
    savings = 0
    debt = 0
    
    for t in totals:
        ctype = t['category_type']
        if ctype == 'income':
            income = t['total']
        elif ctype == 'expense':
            expense = t['total']
        elif ctype == 'savings':
            savings = t['total']
        elif ctype == 'debt':
            debt = t['total']
    
    # Dual Balance Calculation
    net_balance = income - expense
    remaining_balance = net_balance - (savings + debt)
    
    # --- CHART DATA PREPARATION ---
    # 1. Expense Categories Data
    expense_data = expense_transactions.values('category').annotate(category_total=Sum('amount'))
    expense_labels = [item['category'] for item in expense_data]
    expense_values = [float(item['category_total']) for item in expense_data]
    
    # 2. Savings Categories Data
    savings_data = savings_transactions.values('category').annotate(category_total=Sum('amount'))
    savings_labels = [item['category'] for item in savings_data]
    savings_values = [float(item['category_total']) for item in savings_data]
    
    # 3. Overview Bar Chart Data
    overview_labels = ['Income', 'Expense', 'Savings', 'Debt']
    overview_values = [float(income), float(expense), float(savings), float(debt)]
    
    context = {
        'transactions': all_transactions,
        'income_transactions': income_transactions,
        'expense_transactions': expense_transactions,
        'savings_transactions': savings_transactions,
        'debt_transactions': debt_transactions,
        'total_income': income,
        'total_expense': expense,
        'total_savings': savings,
        'total_debt': debt,
        'net_balance': net_balance,
        'remaining_balance': remaining_balance,
        
        # Pass active filters back to the template
        'filter_category_type': filter_category_type,
        'filter_start_date': filter_start_date,
        'filter_end_date': filter_end_date,
        'filter_category': filter_category,
        
        # Chart JSON Data
        'expense_labels_json': json.dumps(expense_labels),
        'expense_values_json': json.dumps(expense_values),
        'savings_labels_json': json.dumps(savings_labels),
        'savings_values_json': json.dumps(savings_values),
        'overview_labels_json': json.dumps(overview_labels),
        'overview_values_json': json.dumps(overview_values),
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            # Auto-populate the old 'type' field based on the selected 'category_type'
            if transaction.category_type == 'income':
                transaction.type = 'income'
            else:
                transaction.type = 'expense'
            transaction.save()
            return redirect('dashboard')
    else:
        form = TransactionForm()
    return render(request, 'tracker/add_transaction.html', {'form': form})
