from django import forms
from .models import Order, OrderItem, Reservation, MenuItem
from datetime import datetime, timedelta


class AddToCartForm(forms.Form):
    """Form for adding items to cart"""
    quantity = forms.IntegerField(
        min_value=1,
        max_value=20,
        widget=forms.Select(choices=[(i, i) for i in range(1, 21)])
    )


class PlaceOrderForm(forms.ModelForm):
    """Form for placing an order"""
    table = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select a table",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Order
        fields = ['order_type', 'table', 'payment_method']
        widgets = {
            'order_type': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Table
        self.fields['table'].queryset = Table.objects.filter(status='Available')
        self.fields['order_type'].label = 'Order Type'
        self.fields['payment_method'].label = 'Payment Method'


class ReservationForm(forms.ModelForm):
    """Form for making table reservations"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        })
    )
    
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = Reservation
        fields = ['name', 'phone', 'email', 'date', 'time', 'guests', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'guests': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '20'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Special requests or dietary needs'
            }),
        }
        labels = {
            'name': 'Name',
            'phone': 'Phone Number',
            'email': 'Email Address',
            'date': 'Reservation Date',
            'time': 'Reservation Time',
            'guests': 'Number of Guests',
            'notes': 'Special Notes',
        }


class OrderFilterForm(forms.Form):
    """Form for filtering orders in admin"""
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(Order.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    order_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Order.ORDER_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class InventoryUpdateForm(forms.Form):
    """Form for updating inventory"""
    ingredient = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingredient name'})
    )
    quantity = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantity'})
    )
    action = forms.ChoiceField(
        choices=[
            ('add', 'Add to Stock'),
            ('set', 'Set Stock Level'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class MenuItemForm(forms.ModelForm):
    """Form for adding/editing menu items"""
    class Meta:
        model = MenuItem
        fields = ['name', 'description', 'price', 'category', 'is_active', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input ms-2'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


# FormSet for managing ingredients for a menu item inline
from django.forms import inlineformset_factory
from .models import MenuItemIngredient

MenuItemIngredientFormSet = inlineformset_factory(
    MenuItem,
    MenuItemIngredient,
    fields=['inventory_item', 'quantity_required'],
    widgets={
        'inventory_item': forms.Select(attrs={'class': 'form-select'}),
        'quantity_required': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
    },
    extra=1,
    can_delete=True
)
