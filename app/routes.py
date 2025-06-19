from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.models.user import User
from app.models.products import Product
from app.models.sales import Sale, SalesItem
from app import db
from datetime import datetime, date, timedelta
from sqlalchemy import func, or_, and_
from functools import wraps

main = Blueprint('main', __name__)

# ============================================================================
# Authentication Decorators
# ============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access the system.', 'error')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# ============================================================================
# Authentication Routes
# ============================================================================

@main.route('/')
def index():
    """Root route - redirects to login if not authenticated, dashboard if logged in"""
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - only way to access the system"""
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session.permanent = True
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    """Logout route"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'{username} logged out successfully.', 'success')
    return redirect(url_for('main.login'))

# ============================================================================
# Main Application Routes
# ============================================================================

@main.route('/dashboard')
@login_required
def dashboard():
    """Dashboard with profit calculations"""
    user = get_current_user()
    
    # Dashboard statistics
    total_products = Product.query.count()
    total_stock_value = db.session.query(
        func.sum(Product.price * Product.stock_level)
    ).scalar() or 0
    low_stock_count = Product.query.filter(Product.stock_level <= 10).count()
    
    # Today's sales and profit
    today = date.today()
    today_revenue = db.session.query(func.sum(Sale.total_amount)).filter(
        func.date(Sale.created_at) == today
    ).scalar() or 0
    
    today_cost = db.session.query(func.sum(Sale.total_cost)).filter(
        func.date(Sale.created_at) == today
    ).scalar() or 0
    
    today_profit = today_revenue - today_cost
    
    # This month's profit
    first_day_of_month = today.replace(day=1)
    month_profit = db.session.query(
        func.sum(Sale.total_amount - Sale.total_cost)
    ).filter(
        func.date(Sale.sale_date) >= first_day_of_month
    ).scalar() or 0
    
    # Low stock products
    low_stock_products = Product.query.filter(Product.stock_level <= 10).all()
    
    # Recent sales for activity
    recent_activities = Sale.query.order_by(Sale.created_at.desc()).limit(10).all()
    
    return render_template('dashboard.html', 
                         user=user,
                         total_products=total_products,
                         total_stock_value=total_stock_value,
                         today_revenue=today_revenue,
                         today_profit=today_profit,
                         month_profit=month_profit,
                         low_stock_count=low_stock_count,
                         low_stock_products=low_stock_products,
                         recent_activities=recent_activities)
@main.route('/inventory')
@login_required
def inventory():
    """Enhanced inventory management with filtering and search"""
    user = get_current_user()
    
    # Get filter parameters
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    stock_status = request.args.get('stock_status', '')
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Build query
    query = Product.query
    
    # Apply search filter
    if search:
        search_filter = or_(
            Product.name.contains(search),
            Product.description.contains(search)
        )
        query = query.filter(search_filter)
    
    # Apply category filter
    if category:
        query = query.filter(Product.category == category)
    
    # Apply stock status filter
    if stock_status == 'low':
        query = query.filter(Product.stock_level <= 10)
    elif stock_status == 'out':
        query = query.filter(Product.stock_level == 0)
    elif stock_status == 'in_stock':
        query = query.filter(Product.stock_level > 10)
    
    # Apply sorting
    if sort_by == 'name':
        sort_column = Product.name
    elif sort_by == 'price':
        sort_column = Product.price
    elif sort_by == 'stock':
        sort_column = Product.stock_level
    elif sort_by == 'category':
        sort_column = Product.category
    else:
        sort_column = Product.created_at
    
    if sort_order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    products = query.all()
    
    # Get all categories for filter dropdown
    categories = db.session.query(Product.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('inventory.html', 
                         products=products, 
                         user=user,
                         categories=categories,
                         current_filters={
                             'search': search,
                             'category': category,
                             'stock_status': stock_status,
                             'sort_by': sort_by,
                             'sort_order': sort_order
                         })

@main.route('/add_product', methods=['POST'])
@login_required
def add_product():
    """Add product"""
    try:
        product = Product(
            name=request.form['name'],
            category=request.form['category'],
            cost=float(request.form.get('cost', 0)),
            price=float(request.form['price']),
            stock_level=int(request.form['stock']),
            description=request.form.get('description', '')
        )
        
        product.save()
        flash(f'Product "{product.name}" added successfully!', 'success')
    except ValueError as e:
        flash(f'Invalid input: Please check your numbers.', 'error')
    except Exception as e:
        flash(f'Error adding product: {str(e)}', 'error')
    
    return redirect(url_for('main.inventory'))

@main.route('/update_stock', methods=['POST'])
@login_required
def update_stock():
    """Update product stock quantity"""
    try:
        product_id = int(request.form['product_id'])
        new_stock = int(request.form['stock_level'])
        
        if new_stock < 0:
            flash('Stock level cannot be negative.', 'error')
            return redirect(url_for('main.inventory'))
        
        product = Product.query.get_or_404(product_id)
        old_stock = product.stock_level
        product.stock_level = new_stock
        product.save()
        
        flash(f'Stock updated for "{product.name}": {old_stock} → {new_stock}', 'success')
    except ValueError:
        flash('Invalid stock level. Please enter a valid number.', 'error')
    except Exception as e:
        flash(f'Error updating stock: {str(e)}', 'error')
    
    return redirect(url_for('main.inventory'))

@main.route('/delete_product/<int:product_id>')
@login_required
def delete_product(product_id):
    """Delete product"""
    try:
        product = Product.query.get_or_404(product_id)
        product_name = product.name
        
        # Delete associated order items first
        sales_items = SalesItem.query.filter_by(product_id=product_id).all()
        for item in sales_items:
            item.delete()
        
        product.delete()
        flash(f'Product "{product_name}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting product: {str(e)}', 'error')
    
    return redirect(url_for('main.inventory'))

@main.route('/sales')
@login_required
def sales():
    """Sales management with authentication"""
    products = Product.query.filter(Product.stock_level > 0).all()
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(50).all()
    user = get_current_user()
    return render_template('sales.html', 
                         products=products, 
                         sales_history=recent_sales, 
                         user=user)

@main.route('/record_sale', methods=['POST'])
@login_required
def record_sale():
    """Record sale with profit tracking"""
    try:
        product_id = int(request.form['product_id'])
        quantity = int(request.form['quantity'])
        payment_type = request.form.get('payment_type', 'Cash')
        
        product = Product.query.get_or_404(product_id)
        
        if not product.is_in_stock(quantity):
            flash(f'Insufficient stock! Only {product.stock_level} units available.', 'error')
            return redirect(url_for('main.sales'))
        
        # Calculate totals
        total_revenue = quantity * product.price
        total_cost = quantity * product.cost  # Use product cost
        total_profit = total_revenue - total_cost
        
        # Create sale record with cost tracking
        sale = Sale(
            total_amount=total_revenue,
            total_cost=total_cost,  # NEW: Store total cost
            payment_type=payment_type
        )
        sale.save()
        
        # Create order item with cost tracking
        order_item = SalesItem(
            sale_id=sale.id,
            product_id=product_id,
            quantity=quantity,
            unit_price=product.price,
            unit_cost=product.cost,  # NEW: Store unit cost
            product_name=product.name
        )
        order_item.save()
        
        # Update product stock
        if product.reduce_stock(quantity):
            product.save()
        
        flash(f'Sale recorded: {quantity}x {product.name} - Revenue: ${total_revenue:.2f}, Profit: ${total_profit:.2f}', 'success')
    except ValueError as e:
        flash('Invalid input: Please check your numbers.', 'error')
    except Exception as e:
        flash(f'Error recording sale: {str(e)}', 'error')
    
    return redirect(url_for('main.sales'))

@main.route('/reports')
@login_required
def reports():
    """Enhanced reports with profit calculations"""
    user = get_current_user()
    
    # Get date filter parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Calculate preset dates
    today = date.today()
    last_7_days = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    last_30_days = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    last_90_days = (today - timedelta(days=90)).strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')
    
    # Set default dates if not provided (last 30 days)
    if not date_from:
        date_from = last_30_days
    if not date_to:
        date_to = today_str
    
    try:
        # Parse dates
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
        
        # Ensure end_date is not before start_date
        if end_date < start_date:
            flash('End date cannot be before start date.', 'error')
            end_date = start_date
            date_to = end_date.strftime('%Y-%m-%d')
        
    except ValueError:
        # If date parsing fails, use defaults
        start_date = today - timedelta(days=30)
        end_date = today
        date_from = start_date.strftime('%Y-%m-%d')
        date_to = end_date.strftime('%Y-%m-%d')
        flash('Invalid date format. Using default date range.', 'error')
    
    # Build date filter for sales
    date_filter = and_(
        func.date(Sale.sale_date) >= start_date,
        func.date(Sale.sale_date) <= end_date
    )
    
    # Calculate filtered statistics including profit
    filtered_sales = Sale.query.filter(date_filter)
    total_revenue = db.session.query(func.sum(Sale.total_amount)).filter(date_filter).scalar() or 0
    total_cost = db.session.query(func.sum(Sale.total_cost)).filter(date_filter).scalar() or 0
    total_profit = total_revenue - total_cost
    total_sales_count = filtered_sales.count()
    avg_sale_value = total_revenue / total_sales_count if total_sales_count > 0 else 0
    avg_profit_per_sale = total_profit / total_sales_count if total_sales_count > 0 else 0
    profit_margin_percentage = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Top selling products with profit (filtered by date)
    top_products = db.session.query(
        Product.name,
        Product.category,
        func.sum(SalesItem.quantity).label('units_sold'),
        func.sum(SalesItem.quantity * SalesItem.unit_price).label('revenue'),
        func.sum(SalesItem.quantity * SalesItem.unit_cost).label('cost'),
        func.sum((SalesItem.unit_price - SalesItem.unit_cost) * SalesItem.quantity).label('profit')
    ).join(SalesItem).join(Sale).filter(date_filter).group_by(Product.id).order_by(
        func.sum((SalesItem.unit_price - SalesItem.unit_cost) * SalesItem.quantity).desc()
    ).limit(10).all()
    
    # Sales by category with profit (filtered by date)
    category_stats = db.session.query(
        Product.category,
        func.sum(SalesItem.quantity).label('units_sold'),
        func.sum(SalesItem.quantity * SalesItem.unit_price).label('revenue'),
        func.sum(SalesItem.quantity * SalesItem.unit_cost).label('cost'),
        func.sum((SalesItem.unit_price - SalesItem.unit_cost) * SalesItem.quantity).label('profit')
    ).join(SalesItem).join(Sale).filter(date_filter).group_by(Product.category).order_by(
        func.sum((SalesItem.unit_price - SalesItem.unit_cost) * SalesItem.quantity).desc()
    ).all()
    
    # Sales by payment type (filtered by date)
    payment_stats = db.session.query(
        Sale.payment_type,
        func.count(Sale.id).label('transaction_count'),
        func.sum(Sale.total_amount).label('revenue'),
        func.sum(Sale.total_cost).label('cost'),
        func.sum(Sale.total_amount - Sale.total_cost).label('profit')
    ).filter(date_filter).group_by(Sale.payment_type).order_by(
        func.sum(Sale.total_amount - Sale.total_cost).desc()
    ).all()
    
    # Calculate comparison with previous period
    period_days = (end_date - start_date).days + 1
    prev_start_date = start_date - timedelta(days=period_days)
    prev_end_date = start_date - timedelta(days=1)
    
    prev_date_filter = and_(
        func.date(Sale.sale_date) >= prev_start_date,
        func.date(Sale.sale_date) <= prev_end_date
    )
    
    prev_revenue = db.session.query(func.sum(Sale.total_amount)).filter(prev_date_filter).scalar() or 0
    prev_cost = db.session.query(func.sum(Sale.total_cost)).filter(prev_date_filter).scalar() or 0
    prev_profit = prev_revenue - prev_cost
    prev_sales_count = Sale.query.filter(prev_date_filter).count()
    
    # Calculate percentage changes
    revenue_change = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
    profit_change = ((total_profit - prev_profit) / prev_profit * 100) if prev_profit > 0 else 0
    sales_change = ((total_sales_count - prev_sales_count) / prev_sales_count * 100) if prev_sales_count > 0 else 0
    
    return render_template('report.html',
                         user=user,
                         total_revenue=total_revenue,
                         total_cost=total_cost,
                         total_profit=total_profit,
                         profit_margin_percentage=profit_margin_percentage,
                         total_sales_count=total_sales_count,
                         avg_sale_value=avg_sale_value,
                         avg_profit_per_sale=avg_profit_per_sale,
                         top_products=top_products,
                         category_stats=category_stats,
                         payment_stats=payment_stats,
                         date_from=date_from,
                         date_to=date_to,
                         period_days=period_days,
                         prev_revenue=prev_revenue,
                         prev_profit=prev_profit,
                         prev_sales_count=prev_sales_count,
                         revenue_change=revenue_change,
                         profit_change=profit_change,
                         sales_change=sales_change,
                         last_7_days=last_7_days,
                         last_30_days=last_30_days,
                         last_90_days=last_90_days,
                         today_str=today_str)


# ============================================================================
# API Routes
# ============================================================================

@main.route('/api/dashboard_data')
@login_required
def api_dashboard_data():
    """API endpoint for dashboard data"""
    total_products = Product.query.count()
    total_stock_value = db.session.query(
        func.sum(Product.price * Product.stock_level)
    ).scalar() or 0
    low_stock_count = Product.query.filter(Product.stock_level <= 10).count()
    
    today = date.today()
    today_sales = db.session.query(func.sum(Sale.total_amount)).filter(
        func.date(Sale.sale_date) == today
    ).scalar() or 0
    
    return jsonify({
        'total_products': total_products,
        'total_stock_value': round(total_stock_value, 2),
        'today_sales': round(today_sales, 2),
        'low_stock_count': low_stock_count
    })

@main.route('/api/product_stock/<int:product_id>')
@login_required
def api_product_stock(product_id):
    """API endpoint to get current product stock"""
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'product_id': product.id,
        'name': product.name,
        'stock_level': product.stock_level,
        'price': product.price
    })

# ============================================================================
# Context Processors
# ============================================================================

@main.app_context_processor
def inject_user():
    """Make current user available in all templates"""
    return dict(current_user=get_current_user())
