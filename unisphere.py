from init_db import init_db
from models import (
    add_accommodation,
    add_accommodation_amenity,
    add_accommodation_photo,
    add_accommodation_video,
    approve_listing,
    authenticate_user,
    create_announcement,
    create_report,
    create_user,
    get_accommodation_amenities,
    get_accommodations,
    get_accommodations_by_landlord,
    get_analytics_dashboard,
    get_or_create_amenity,
    get_users,
    mark_listing_suspicious,
    update_homepage_content,
)

init_db()

print('Creating sample users...')
admin_id = create_user('Admin User', 'admin@example.com', 'Password123!', 'admin')
landlord_id = create_user('Landlord User', 'landlord@example.com', 'Password123!', 'landlord')
user_id = create_user('Regular User', 'user@example.com', 'Password123!', 'user')
print(f'Users created: admin={admin_id}, landlord={landlord_id}, user={user_id}')
print('All users:', get_users())

print('\nCreating sample accommodations...')
acc1 = add_accommodation(
    name='Modern Apartment Downtown',
    description='3 bedroom apartment in city center',
    price=1500,
    location='123 Main St, City',
    owner_id=landlord_id,
    latitude=40.7128,
    longitude=-74.0060,
    availability_option='rent',
    vacancy_status='vacant',
    units_available=2,
    is_student_accommodation=False,
)
print(f'Accommodation 1 created: {acc1}')

acc2 = add_accommodation(
    name='Student Housing Complex',
    description='Affordable housing for students',
    price=800,
    location='456 Campus Ave, College Town',
    owner_id=landlord_id,
    latitude=40.8075,
    longitude=-73.9626,
    availability_option='rent',
    vacancy_status='vacant',
    units_available=5,
    is_student_accommodation=True,
)
print(f'Accommodation 2 created: {acc2}')

print('\nGeneral public accommodations:')
public_accs = get_accommodations(is_student_accommodation=False)
print(f'Found {len(public_accs)} public accommodations')

print('\nStudent accommodations:')
student_accs = get_accommodations(is_student_accommodation=True)
print(f'Found {len(student_accs)} student accommodations')

print('\nAdding amenities to accommodation 1...')
mall_amenity = get_or_create_amenity('Downtown Shopping Mall', 'mall')
restaurant_amenity = get_or_create_amenity('Italian Restaurant', 'restaurant')
add_accommodation_amenity(acc1, mall_amenity, distance_km=0.5)
add_accommodation_amenity(acc1, restaurant_amenity, distance_km=0.2)
amenities = get_accommodation_amenities(acc1)
print(f'Amenities for accommodation 1: {amenities}')

print('\nAdding photos to accommodation 1...')
photo1 = add_accommodation_photo(
    acc1,
    'https://example.com/photo1.jpg',
    'Front view of apartment'
)
photo2 = add_accommodation_photo(
    acc1,
    'https://example.com/photo2.jpg',
    'Living room'
)
print(f'Photos added: {photo1}, {photo2}')

print('\nAdding video to accommodation 1...')
video1 = add_accommodation_video(
    acc1,
    'https://example.com/virtual-tour.mp4',
    'Virtual tour of apartment'
)
print(f'Video added: {video1}')

print('\nLandlord accommodations:')
landlord_accs = get_accommodations_by_landlord(landlord_id)
print(f'Landlord has {len(landlord_accs)} accommodations')

print('\nAuthenticating landlord...')
user = authenticate_user('landlord@example.com', 'Password123!')
print(f'Login successful: {user}')

print('\n' + '='*60)
print('DEMONSTRATING ADMIN FEATURES')
print('='*60)

print('\nApproving listings...')
approve_listing(acc1)
print(f'✅ Listing {acc1} approved for publication')

print('\nMarking listing as suspicious (for demo purposes)...')
mark_listing_suspicious(acc2, 'Unusual pricing pattern detected')
print(f'⚠️  Listing {acc2} marked as suspicious for review')

print('\nCreating sample reports...')
report1 = create_report(
    report_type='suspicious_listing',
    reason='Prices seem unrealistic',
    description='Property priced significantly below market value',
    reporter_id=user_id,
    reported_accommodation_id=acc2
)
print(f'📋 Report created: {report1}')

report2 = create_report(
    report_type='user_violation',
    reason='Abusive communication',
    description='Landlord sent inappropriate messages',
    reporter_id=user_id,
    reported_user_id=landlord_id
)
print(f'📋 Report created: {report2}')

print('\nCreating announcements...')
announce1 = create_announcement(
    title='Platform Maintenance',
    content='System maintenance scheduled for 2:00-2:30 AM UTC',
    announcement_type='maintenance',
    created_by=admin_id
)
print(f'📢 Announcement created: {announce1}')

announce2 = create_announcement(
    title='Housing Alert - High Demand Areas',
    content='Properties in downtown areas are selling quickly!',
    announcement_type='alert',
    created_by=admin_id
)
print(f'📢 Announcement created: {announce2}')

print('\nUpdating homepage content...')
update_homepage_content(
    'hero_section',
    'Find Your Perfect Home Today - Browse 1000s of Properties',
    admin_id
)
update_homepage_content(
    'features_section',
    'Virtual Tours • Amenity Discovery • Instant Messaging • Verified Listings',
    admin_id
)
print('✅ Homepage content updated')

print('\n' + '='*60)
print('ANALYTICS DASHBOARD')
print('='*60)
analytics = get_analytics_dashboard()
print('\nPlatform Statistics:')
for key, value in analytics.items():
    print(f'  {key}: {value}')

print('\n' + '='*60)
print('Test completed successfully! ✅')
print('='*60)
