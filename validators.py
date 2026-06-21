"""Input validation utilities for API endpoints."""

from config import (
    MAX_PRICE,
    MAX_DISTANCE_KM,
    MAX_STRING_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
import re


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_email(email):
    """Validate email format."""
    if not email or not isinstance(email, str):
        raise ValidationError('email is required and must be a string')
    if len(email) > MAX_STRING_LENGTH:
        raise ValidationError(f'email must be less than {MAX_STRING_LENGTH} characters')
    
    # Simple email regex (RFC 5322 simplified)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError('invalid email format')
    return email


def validate_password(password):
    """Validate password strength."""
    if not password or not isinstance(password, str):
        raise ValidationError('password is required and must be a string')
    if len(password) < 8:
        raise ValidationError('password must be at least 8 characters long')
    if len(password) > MAX_STRING_LENGTH:
        raise ValidationError(f'password must be less than {MAX_STRING_LENGTH} characters')
    return password


def validate_name(name):
    """Validate user/accommodation name."""
    if not name or not isinstance(name, str):
        raise ValidationError('name is required and must be a string')
    name = name.strip()
    if len(name) < 2:
        raise ValidationError('name must be at least 2 characters long')
    if len(name) > MAX_STRING_LENGTH:
        raise ValidationError(f'name must be less than {MAX_STRING_LENGTH} characters')
    return name


def validate_price(price):
    """Validate accommodation price."""
    try:
        price = float(price)
    except (ValueError, TypeError):
        raise ValidationError('price must be a valid number')
    
    if price < 0:
        raise ValidationError('price cannot be negative')
    if price > MAX_PRICE:
        raise ValidationError(f'price cannot exceed {MAX_PRICE}')
    return price


def validate_distance_km(distance):
    """Validate distance in kilometers."""
    try:
        distance = float(distance)
    except (ValueError, TypeError):
        raise ValidationError('distance must be a valid number')
    
    if distance < 0:
        raise ValidationError('distance cannot be negative')
    if distance > MAX_DISTANCE_KM:
        raise ValidationError(f'distance cannot exceed {MAX_DISTANCE_KM} km')
    return distance


def validate_latitude(latitude):
    """Validate latitude coordinate."""
    try:
        latitude = float(latitude)
    except (ValueError, TypeError):
        raise ValidationError('latitude must be a valid number')
    
    if latitude < -90 or latitude > 90:
        raise ValidationError('latitude must be between -90 and 90')
    return latitude


def validate_longitude(longitude):
    """Validate longitude coordinate."""
    try:
        longitude = float(longitude)
    except (ValueError, TypeError):
        raise ValidationError('longitude must be a valid number')
    
    if longitude < -180 or longitude > 180:
        raise ValidationError('longitude must be between -180 and 180')
    return longitude


def validate_description(description):
    """Validate description text."""
    if not description or not isinstance(description, str):
        raise ValidationError('description is required and must be a string')
    description = description.strip()
    if len(description) < 10:
        raise ValidationError('description must be at least 10 characters long')
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValidationError(f'description must be less than {MAX_DESCRIPTION_LENGTH} characters')
    return description


def validate_location(location):
    """Validate location string."""
    if not location or not isinstance(location, str):
        raise ValidationError('location is required and must be a string')
    location = location.strip()
    if len(location) < 3:
        raise ValidationError('location must be at least 3 characters long')
    if len(location) > MAX_STRING_LENGTH:
        raise ValidationError(f'location must be less than {MAX_STRING_LENGTH} characters')
    return location


def validate_availability_option(option):
    """Validate accommodation availability option."""
    valid_options = ['buy', 'rent', 'both']
    if option not in valid_options:
        raise ValidationError(f'availability_option must be one of {valid_options}')
    return option


def validate_vacancy_status(status):
    """Validate vacancy status."""
    valid_statuses = ['vacant', 'occupied', 'maintenance']
    if status not in valid_statuses:
        raise ValidationError(f'vacancy_status must be one of {valid_statuses}')
    return status


def validate_role(role):
    """Validate user role."""
    valid_roles = ['user', 'landlord', 'school', 'admin']
    if role not in valid_roles:
        raise ValidationError(f'role must be one of {valid_roles}')
    return role


def validate_amenity_category(category):
    """Validate amenity category."""
    valid_categories = ['mall', 'restaurant', 'other']
    if category not in valid_categories:
        raise ValidationError(f'category must be one of {valid_categories}')
    return category


def validate_announcement_type(announcement_type):
    """Validate announcement type."""
    valid_types = ['alert', 'maintenance', 'notice']
    if announcement_type not in valid_types:
        raise ValidationError(f'announcement_type must be one of {valid_types}')
    return announcement_type


def validate_page_size(page_size):
    """Validate and constrain page size."""
    try:
        page_size = int(page_size)
    except (ValueError, TypeError):
        page_size = DEFAULT_PAGE_SIZE
    
    if page_size < 1:
        page_size = DEFAULT_PAGE_SIZE
    if page_size > MAX_PAGE_SIZE:
        page_size = MAX_PAGE_SIZE
    
    return page_size


def validate_page_number(page):
    """Validate page number."""
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    
    if page < 1:
        page = 1
    
    return page


def validate_units_available(units):
    """Validate units available count."""
    try:
        units = int(units)
    except (ValueError, TypeError):
        raise ValidationError('units_available must be an integer')
    
    if units < 0:
        raise ValidationError('units_available cannot be negative')
    if units > 10000:
        raise ValidationError('units_available cannot exceed 10000')
    
    return units
