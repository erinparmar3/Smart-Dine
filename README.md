# SmartDine - Restaurant Management System

A comprehensive Django-based restaurant management system with digital ordering, reservation management, inventory tracking, and an admin dashboard.

## Features

### Customer Features
- **Browse Menu**: Explore restaurant menu with beautiful images and descriptions
- **Digital Ordering**: Add items to cart and place orders with multiple order types (Dine-in, Delivery, Pickup)
- **Payment Options**: Support for multiple payment methods (Card, UPI, Cash)
- **Order Tracking**: Easily track order status and confirmation
- **Table Reservations**: Book tables in advance with flexible date/time options

### Admin Features
- **Order Management**: View, filter, and update order statuses
- **Inventory Management**: Track ingredient stock levels with low-stock alerts
- **Table Management**: Monitor table status and reservation details
- **Real-time Dashboard**: View orders, revenue, and key metrics
- **Historical Data**: Access complete order and reservation history

## Technology Stack

- **Backend**: Django 6.0.2 (Python)
- **Database**: SQLite (Development)
- **Frontend**: HTML5, CSS3, JavaScript
- **Framework**: Bootstrap 5.3
- **Icons**: Font Awesome 6.0

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package installer)
- Git (optional)

### Setup Steps

1. **Navigate to project directory**
   ```bash
   cd "a:\DDU\SEM 4\PYTHON\Django\smartdine"
   ```

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install django
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Load sample data**
   ```bash
   python manage.py load_sample_data
   ```

6. **Create a superuser (admin account)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Application: http://127.0.0.1:8000/
   - Admin Panel: http://127.0.0.1:8000/admin/

## Usage

### For Customers

1. **Viewing Menu**
   - Go to "Menu & Order" section
   - Browse available dishes with prices and descriptions
   - View images and category information

2. **Placing an Order**
   - Select items and quantities from the menu
   - Add items to cart
   - Choose order type (Dine-in, Delivery, or Pickup)
   - Select payment method
   - For Dine-in orders, choose a table
   - Click "Checkout & Pay"

3. **Making a Reservation**
   - Go to "Reservations" section
   - Fill in your Name, Phone, Email
   - Select desired Date and Time
   - Enter number of guests
   - Add any special requests
   - Submit the form

4. **Tracking Orders**
   - After placing an order, you'll see a confirmation page
   - Order ID and status are displayed
   - Check admin dashboard for order status updates

### For Administrators

1. **Dashboard**
   - View key metrics (Today's orders, revenue, pending orders)
   - See recent orders and low stock alerts
   - Quick access to all management sections

2. **Managing Orders**
   - View all orders with detailed information
   - Filter by status or order type
   - Update order status (Pending → Preparing → Ready → Completed)
   - Track payment method and order type

3. **Inventory Management**
   - Monitor stock levels for all ingredients
   - Receive alerts for low stock items
   - Add new ingredients or update quantities
   - Track last update timestamps

4. **Table Management**
   - View all table information
   - Update table status (Available/Occupied/Reserved)
   - Monitor table reservations
   - See table capacity and availability

5. **Reservation Management**
   - View all reservation requests
   - Confirm reservations with automatic table assignment
   - See guest contact information and special requests
   - Track reservation statistics

## Project Structure

```
smartdine/
├── smartdine/                 # Main project settings
│   ├── settings.py           # Django configuration
│   ├── urls.py               # Main URL configuration
│   └── wsgi.py               # WSGI configuration
├── home/                      # Main app
│   ├── models.py             # Database models
│   ├── views.py              # View functions
│   ├── urls.py               # App URL patterns
│   ├── forms.py              # Django forms
│   ├── admin.py              # Django admin configuration
│   ├── management/           # Management commands
│   │   └── commands/
│   │       └── load_sample_data.py
│   └── templatetags/         # Custom template filters
│       └── custom_filters.py
├── templates/                # HTML templates
│   ├── base.html            # Base template
│   ├── index.html           # Home page
│   ├── menu.html            # Menu page
│   ├── reservations.html    # Reservations page
│   ├── order_confirmation.html
│   └── admin/               # Admin templates
│       ├── dashboard.html
│       ├── orders.html
│       ├── inventory.html
│       ├── tables.html
│       └── reservations.html
├── static/                   # Static files
│   ├── css/
│   │   └── style.css        # Main stylesheet
│   └── js/
│       └── script.js        # Main JavaScript
├── manage.py                # Django management script
└── db.sqlite3              # SQLite database
```

## Database Models

### MenuItem
- Store restaurant menu items
- Fields: name, price, category, image, description

### Order
- Track customer orders
- Fields: order_id, order_type, table, payment_method, total, status, timestamps

### OrderItem
- Individual items in an order
- Fields: order, menu_item, quantity, price

### Reservation
- Table reservations
- Fields: name, phone, email, date, time, guests, table, notes

### Table
- Restaurant tables
- Fields: table_number, capacity, status

### InventoryItem
- Ingredient inventory
- Fields: name, quantity, unit, reorder_level, last_updated

### Recipe
- Menu item recipes
- Fields: menu_item

### RecipeIngredient
- Individual ingredients in recipes
- Fields: recipe, ingredient, quantity

## Key Django URLs

| URL | View | Purpose |
|-----|------|---------|
| `/` | index | Home page |
| `/menu/` | menu | Browse and order items |
| `/add-to-cart/` | add_to_cart | Add item to cart |
| `/place-order/` | place_order | Complete order |
| `/reservations/` | reservations | Make reservation |
| `/admin/` | admin_dashboard | Admin dashboard |
| `/admin/orders/` | admin_orders | Manage orders |
| `/admin/inventory/` | admin_inventory | Manage inventory |
| `/admin/tables/` | admin_tables | Manage tables |

## Sample Data

The project includes sample data:
- 6 Menu items (Pizza, Biryani, Coffee, Salad, Pasta, Cake)
- 6 Restaurant tables (capacity 2-4)
- 12 Inventory items (Flour, Cheese, Spices, etc.)

Load with: `python manage.py load_sample_data`

## Customization

### Adding More Menu Items
1. Go to Django admin at `/admin/`
2. Add new Menu Items
3. Create Recipe and RecipeIngredient for inventory tracking

### Modifying Inventory
1. Use Admin Inventory page
2. Add, update, or set stock levels
3. System automatically alerts when stock is low

### Changing Table Configuration
1. Modify Table model or use Django admin
2. Update table numbers, capacity, and status
3. Changes reflect in customer's table selection

## Common Tasks

### Create Admin User
```bash
python manage.py createsuperuser
```

### Access Django Admin
Navigate to: http://127.0.0.1:8000/admin/

### Clear Cart (User-side)
- Click "Clear Cart" button on Menu page
- Cart session data is cleared

### View Database
Use Django ORM in shell:
```bash
python manage.py shell
from home.models import *
Order.objects.all()
MenuItem.objects.all()
```

## Troubleshooting

### Port Already in Use
```bash
python manage.py runserver 0.0.0.0:8001
```

### Template Not Found
- Check `TEMPLATES` setting in `settings.py`
- Verify template file exists in `templates/` folder
- Restart development server

### Static Files Not Loading
- Place files in `static/` folder
- Use `{% load static %}` in template
- Add to template: `{% static 'path/to/file' %}`

### Database Issues
- Delete `db.sqlite3` and `.migrations/` (except `__init__.py`)
- Run `python manage.py migrate` again
- Run `python manage.py load_sample_data`

## Performance Tips

1. **Use select_related() and prefetch_related()** for database queries
2. **Cache frequently accessed data** using Django's cache framework
3. **Optimize images** for faster loading
4. **Use async tasks** for inventory deduction

## Security Considerations

1. **Change SECRET_KEY** in production
2. **Set DEBUG = False** in production
3. **Use environment variables** for sensitive settings
4. **Implement authentication** for admin views
5. **Validate all user inputs**
6. **Use HTTPS** in production
7. **Set ALLOWED_HOSTS** properly

## Future Enhancements

- [ ] User authentication and accounts
- [ ] Payment gateway integration
- [ ] Email notifications
- [ ] SMS alerts
- [ ] Multi-language support
- [ ] Mobile app
- [ ] Real-time order updates with WebSockets
- [ ] Analytics and reports
- [ ] QR code for table orders
- [ ] Loyalty program
- [ ] Kitchen display system (KDS)
- [ ] Customer reviews and ratings

## API Documentation

The application uses Django built-in forms and views. Future REST API endpoints could include:
- `/api/menu/` - Get menu items
- `/api/orders/` - Orders management
- `/api/reservations/` - Reservations management
- `/api/inventory/` - Inventory tracking

## Support and Contact

For issues or questions:
1. Check Django documentation: https://docs.djangoproject.com/
2. Review code comments and docstrings
3. Check template error messages
4. Enable DEBUG mode for detailed error pages

## License

This project is created for educational purposes.

## Changelog

### Version 1.0 (Initial Release)
- Complete menu management system
- Digital ordering system
- Table reservation system
- Inventory tracking
- Admin dashboard
- Order management
- All core features implemented

---

**Last Updated:** February 8, 2026
**Django Version:** 6.0.2
**Python Version:** 3.13+
