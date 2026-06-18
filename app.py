import os
from functools import wraps

from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required

from config import JWT_ACCESS_TOKEN_EXPIRES, JWT_SECRET_KEY
from init_db import init_db
from models import (
    add_accommodation,
    add_accommodation_amenity,
    add_accommodation_photo,
    add_accommodation_video,
    approve_listing,
    authenticate_user,
    create_announcement,
    create_password_reset_token,
    create_report,
    create_user,
    create_verification_token,
    deactivate_announcement,
    delete_user,
    edit_listing,
    get_accommodation,
    get_accommodation_amenities,
    get_accommodation_photos,
    get_accommodation_videos,
    get_accommodations,
    get_accommodations_by_landlord,
    get_all_listings,
    get_analytics_dashboard,
    get_announcements,
    get_homepage_content,
    get_or_create_amenity,
    get_report,
    get_reports,
    get_user_by_id,
    get_users,
    mark_listing_suspicious,
    reactivate_user,
    reject_listing,
    resolve_report,
    reset_password,
    search_users,
    suspend_user,
    unmark_listing_suspicious,
    unverify_landlord,
    update_accommodation,
    update_homepage_content,
    verify_landlord,
    verify_user_email,
)

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_ACCESS_TOKEN_EXPIRES
jwt = JWTManager(app)


def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            identity = get_jwt_identity()
            if not identity or identity.get('role') not in allowed_roles:
                return jsonify({'error': 'forbidden'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ==== AUTHENTICATION ====

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json(silent=True) or {}
    required = ['name', 'email', 'password', 'role']
    if not all(field in data for field in required):
        return (
            jsonify({'error': 'name, email, password and role are required'}),
            400,
        )
    role = data['role']
    if role not in ['user', 'landlord']:
        return (jsonify({'error': 'invalid role'}), 400)
    user_id = create_user(data['name'], data['email'], data['password'], role)
    token = create_verification_token(user_id)
    return jsonify(
        {
            'status': 'user created',
            'email_verification_token': token,
            'message': 'Use the token with /verify-email to complete registration',
        }
    ), 201


@app.route('/register-admin', methods=['POST'])
@role_required('admin')
def register_admin():
    data = request.get_json(silent=True) or {}
    required = ['name', 'email', 'password']
    if not all(field in data for field in required):
        return (jsonify({'error': 'name, email and password are required'}), 400)
    user_id = create_user(data['name'], data['email'], data['password'], 'admin')
    token = create_verification_token(user_id)
    return jsonify(
        {
            'status': 'admin user created',
            'email_verification_token': token,
        }
    ), 201


@app.route('/verify-email', methods=['POST'])
def verify_email():
    data = request.get_json(silent=True) or {}
    token = data.get('token')
    if not token:
        return jsonify({'error': 'token is required'}), 400
    if not verify_user_email(token):
        return jsonify({'error': 'invalid or expired token'}), 400
    return jsonify({'status': 'email verified'}), 200


@app.route('/request-password-reset', methods=['POST'])
def request_password_reset():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    if not email:
        return jsonify({'error': 'email is required'}), 400
    token = create_password_reset_token(email)
    if not token:
        return jsonify({'status': 'if the account exists, a reset link was sent'}), 200
    return jsonify(
        {
            'status': 'password reset token created',
            'reset_token': token,
            'message': 'Use this token with /reset-password',
        }
    ), 200


@app.route('/reset-password', methods=['POST'])
def reset_password_route():
    data = request.get_json(silent=True) or {}
    token = data.get('token')
    new_password = data.get('password')
    if not token or not new_password:
        return jsonify({'error': 'token and password are required'}), 400
    if not reset_password(token, new_password):
        return jsonify({'error': 'invalid or expired token'}), 400
    return jsonify({'status': 'password has been reset'}), 200


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'email and password are required'}), 400
    user = authenticate_user(data['email'], data['password'])
    if not user:
        return jsonify({'error': 'invalid credentials or email not verified'}), 401
    token = create_access_token(identity=user)
    return jsonify({'access_token': token, 'user': user})


# ==== USER MANAGEMENT ====

@app.route('/users', methods=['GET'])
@role_required('admin')
def list_users():
    return jsonify(get_users())


@app.route('/users/search', methods=['GET'])
@role_required('admin')
def search_users_route():
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify({'error': 'search query must be at least 2 characters'}), 400
    return jsonify(search_users(query))


@app.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    identity = get_jwt_identity()
    if identity['role'] != 'admin' and identity['id'] != user_id:
        return jsonify({'error': 'forbidden'}), 403
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'not found'}), 404
    return jsonify(user)


@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    identity = get_jwt_identity()
    return jsonify(identity)


@app.route('/users/<int:user_id>/suspend', methods=['POST'])
@role_required('admin')
def suspend_user_route(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'user not found'}), 404
    suspend_user(user_id)
    return jsonify({'status': 'user suspended'}), 200


@app.route('/users/<int:user_id>/reactivate', methods=['POST'])
@role_required('admin')
def reactivate_user_route(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'user not found'}), 404
    reactivate_user(user_id)
    return jsonify({'status': 'user reactivated'}), 200


@app.route('/users/<int:user_id>/delete', methods=['POST'])
@role_required('admin')
def delete_user_route(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'user not found'}), 404
    delete_user(user_id)
    return jsonify({'status': 'user deleted'}), 200


@app.route('/users/<int:user_id>/verify-landlord', methods=['POST'])
@role_required('admin')
def verify_landlord_route(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'user not found'}), 404
    if user['role'] != 'landlord':
        return jsonify({'error': 'user is not a landlord'}), 400
    verify_landlord(user_id)
    return jsonify({'status': 'landlord verified'}), 200


@app.route('/users/<int:user_id>/unverify-landlord', methods=['POST'])
@role_required('admin')
def unverify_landlord_route(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'user not found'}), 404
    if user['role'] != 'landlord':
        return jsonify({'error': 'user is not a landlord'}), 400
    unverify_landlord(user_id)
    return jsonify({'status': 'landlord unverified'}), 200


# ==== ACCOMMODATIONS ====

@app.route('/accommodations', methods=['GET'])
def list_accommodations():
    is_student = request.args.get('student', 'false').lower() == 'true'
    availability = request.args.get('availability')
    vacancy = request.args.get('vacancy')
    return jsonify(
        get_accommodations(
            is_student_accommodation=is_student,
            availability_option=availability,
            vacancy_status=vacancy,
        )
    )


@app.route('/accommodations/<int:accommodation_id>', methods=['GET'])
def get_accommodation_detail(accommodation_id):
    acc = get_accommodation(accommodation_id)
    if not acc:
        return jsonify({'error': 'not found'}), 404
    acc['amenities'] = get_accommodation_amenities(accommodation_id)
    acc['photos'] = get_accommodation_photos(accommodation_id)
    acc['videos'] = get_accommodation_videos(accommodation_id)
    return jsonify(acc)


@app.route('/accommodations', methods=['POST'])
@role_required('admin', 'landlord')
def create_accommodation():
    data = request.get_json(silent=True) or {}
    required = ['name', 'description', 'price', 'location', 'availability_option']
    if not all(field in data for field in required):
        return (
            jsonify({'error': 'name, description, price, location and availability_option are required'}),
            400,
        )
    if data['availability_option'] not in ['buy', 'rent', 'both']:
        return jsonify({'error': 'availability_option must be buy, rent, or both'}), 400
    identity = get_jwt_identity()
    acc_id = add_accommodation(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        location=data['location'],
        owner_id=identity['id'],
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        availability_option=data['availability_option'],
        vacancy_status=data.get('vacancy_status', 'vacant'),
        units_available=data.get('units_available', 1),
        is_student_accommodation=data.get('is_student_accommodation', False),
    )
    return jsonify({'status': 'accommodation created', 'id': acc_id}), 201


@app.route('/accommodations/<int:accommodation_id>', methods=['PUT'])
@jwt_required()
def update_accommodation_route(accommodation_id):
    identity = get_jwt_identity()
    acc = get_accommodation(accommodation_id)
    if not acc:
        return jsonify({'error': 'not found'}), 404
    if identity['role'] != 'admin' and acc['owner_id'] != identity['id']:
        return jsonify({'error': 'forbidden'}), 403
    data = request.get_json(silent=True) or {}
    update_accommodation(accommodation_id, **data)
    return jsonify({'status': 'accommodation updated'}), 200


@app.route('/my-accommodations', methods=['GET'])
@role_required('admin', 'landlord')
def my_accommodations():
    identity = get_jwt_identity()
    accs = get_accommodations_by_landlord(identity['id'])
    return jsonify(accs)


# ==== LISTING MANAGEMENT (ADMIN) ====

@app.route('/admin/listings', methods=['GET'])
@role_required('admin')
def admin_view_listings():
    approval_status = request.args.get('status')
    return jsonify(get_all_listings(approval_status))


@app.route('/admin/listings/<int:listing_id>/approve', methods=['POST'])
@role_required('admin')
def admin_approve_listing(listing_id):
    acc = get_accommodation(listing_id)
    if not acc:
        return jsonify({'error': 'listing not found'}), 404
    approve_listing(listing_id)
    return jsonify({'status': 'listing approved'}), 200


@app.route('/admin/listings/<int:listing_id>/reject', methods=['POST'])
@role_required('admin')
def admin_reject_listing(listing_id):
    data = request.get_json(silent=True) or {}
    reason = data.get('reason', 'No reason provided')
    acc = get_accommodation(listing_id)
    if not acc:
        return jsonify({'error': 'listing not found'}), 404
    reject_listing(listing_id, reason)
    return jsonify({'status': 'listing rejected'}), 200


@app.route('/admin/listings/<int:listing_id>/mark-suspicious', methods=['POST'])
@role_required('admin')
def admin_mark_suspicious(listing_id):
    data = request.get_json(silent=True) or {}
    reason = data.get('reason', 'Suspicious activity detected')
    acc = get_accommodation(listing_id)
    if not acc:
        return jsonify({'error': 'listing not found'}), 404
    mark_listing_suspicious(listing_id, reason)
    return jsonify({'status': 'listing marked suspicious'}), 200


@app.route('/admin/listings/<int:listing_id>/unmark-suspicious', methods=['POST'])
@role_required('admin')
def admin_unmark_suspicious(listing_id):
    acc = get_accommodation(listing_id)
    if not acc:
        return jsonify({'error': 'listing not found'}), 404
    unmark_listing_suspicious(listing_id)
    return jsonify({'status': 'listing unmarked suspicious'}), 200


@app.route('/admin/listings/<int:listing_id>/edit', methods=['PUT'])
@role_required('admin')
def admin_edit_listing(listing_id):
    acc = get_accommodation(listing_id)
    if not acc:
        return jsonify({'error': 'listing not found'}), 404
    data = request.get_json(silent=True) or {}
    edit_listing(listing_id, **data)
    return jsonify({'status': 'listing updated'}), 200


# ==== PHOTOS ====

@app.route('/accommodations/<int:accommodation_id>/photos', methods=['POST'])
@jwt_required()
def upload_photo(accommodation_id):
    identity = get_jwt_identity()
    acc = get_accommodation(accommodation_id)
    if not acc:
        return jsonify({'error': 'accommodation not found'}), 404
    if identity['role'] != 'admin' and acc['owner_id'] != identity['id']:
        return jsonify({'error': 'forbidden'}), 403
    data = request.get_json(silent=True) or {}
    photo_url = data.get('photo_url')
    if not photo_url:
        return jsonify({'error': 'photo_url is required'}), 400
    photo_id = add_accommodation_photo(accommodation_id, photo_url, data.get('description'))
    return jsonify({'status': 'photo uploaded', 'id': photo_id}), 201


@app.route('/accommodations/<int:accommodation_id>/photos', methods=['GET'])
def get_photos(accommodation_id):
    return jsonify(get_accommodation_photos(accommodation_id))


# ==== VIDEOS ====

@app.route('/accommodations/<int:accommodation_id>/videos', methods=['POST'])
@jwt_required()
def upload_video(accommodation_id):
    identity = get_jwt_identity()
    acc = get_accommodation(accommodation_id)
    if not acc:
        return jsonify({'error': 'accommodation not found'}), 404
    if identity['role'] != 'admin' and acc['owner_id'] != identity['id']:
        return jsonify({'error': 'forbidden'}), 403
    data = request.get_json(silent=True) or {}
    video_url = data.get('video_url')
    if not video_url:
        return jsonify({'error': 'video_url is required'}), 400
    video_id = add_accommodation_video(accommodation_id, video_url, data.get('title'))
    return jsonify({'status': 'video uploaded', 'id': video_id}), 201


@app.route('/accommodations/<int:accommodation_id>/videos', methods=['GET'])
def get_videos(accommodation_id):
    return jsonify(get_accommodation_videos(accommodation_id))


# ==== AMENITIES ====

@app.route('/accommodations/<int:accommodation_id>/amenities', methods=['POST'])
@jwt_required()
def add_amenity_to_accommodation(accommodation_id):
    identity = get_jwt_identity()
    acc = get_accommodation(accommodation_id)
    if not acc:
        return jsonify({'error': 'accommodation not found'}), 404
    if identity['role'] != 'admin' and acc['owner_id'] != identity['id']:
        return jsonify({'error': 'forbidden'}), 403
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    category = data.get('category')
    distance_km = data.get('distance_km')
    if not name or not category:
        return jsonify({'error': 'name and category are required'}), 400
    if category not in ['mall', 'restaurant', 'other']:
        return jsonify({'error': 'category must be mall, restaurant, or other'}), 400
    amenity_id = get_or_create_amenity(name, category)
    add_accommodation_amenity(accommodation_id, amenity_id, distance_km)
    return jsonify({'status': 'amenity added', 'amenity_id': amenity_id}), 201


@app.route('/accommodations/<int:accommodation_id>/amenities', methods=['GET'])
def get_amenities(accommodation_id):
    return jsonify(get_accommodation_amenities(accommodation_id))


# ==== REPORTS ====

@app.route('/reports', methods=['POST'])
@jwt_required()
def create_report_route():
    identity = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    report_type = data.get('report_type')
    reason = data.get('reason')
    if not report_type or not reason:
        return jsonify({'error': 'report_type and reason are required'}), 400
    report_id = create_report(
        report_type=report_type,
        reason=reason,
        description=data.get('description'),
        reporter_id=identity['id'],
        reported_user_id=data.get('reported_user_id'),
        reported_accommodation_id=data.get('reported_accommodation_id'),
    )
    return jsonify({'status': 'report created', 'id': report_id}), 201


@app.route('/admin/reports', methods=['GET'])
@role_required('admin')
def admin_view_reports():
    status = request.args.get('status')
    return jsonify(get_reports(status))


@app.route('/admin/reports/<int:report_id>', methods=['GET'])
@role_required('admin')
def admin_get_report(report_id):
    report = get_report(report_id)
    if not report:
        return jsonify({'error': 'report not found'}), 404
    return jsonify(report)


@app.route('/admin/reports/<int:report_id>/resolve', methods=['POST'])
@role_required('admin')
def admin_resolve_report(report_id):
    data = request.get_json(silent=True) or {}
    resolution_notes = data.get('resolution_notes', '')
    report = get_report(report_id)
    if not report:
        return jsonify({'error': 'report not found'}), 404
    resolve_report(report_id, resolution_notes)
    return jsonify({'status': 'report resolved'}), 200


# ==== ANALYTICS ====

@app.route('/admin/analytics', methods=['GET'])
@role_required('admin')
def admin_analytics():
    return jsonify(get_analytics_dashboard())


# ==== ANNOUNCEMENTS ====

@app.route('/announcements', methods=['GET'])
def get_announcements_route():
    announcement_type = request.args.get('type')
    return jsonify(get_announcements(announcement_type))


@app.route('/admin/announcements', methods=['POST'])
@role_required('admin')
def admin_create_announcement():
    identity = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    required = ['title', 'content', 'announcement_type']
    if not all(field in data for field in required):
        return jsonify({'error': 'title, content, and announcement_type are required'}), 400
    if data['announcement_type'] not in ['alert', 'maintenance', 'notice']:
        return jsonify({'error': 'invalid announcement_type'}), 400
    announcement_id = create_announcement(
        title=data['title'],
        content=data['content'],
        announcement_type=data['announcement_type'],
        created_by=identity['id']
    )
    return jsonify({'status': 'announcement created', 'id': announcement_id}), 201


@app.route('/admin/announcements/<int:announcement_id>/deactivate', methods=['POST'])
@role_required('admin')
def admin_deactivate_announcement(announcement_id):
    deactivate_announcement(announcement_id)
    return jsonify({'status': 'announcement deactivated'}), 200


# ==== HOMEPAGE CONTENT ====

@app.route('/homepage/content', methods=['GET'])
def get_homepage_content_route():
    section = request.args.get('section')
    return jsonify(get_homepage_content(section))


@app.route('/admin/homepage/content', methods=['POST'])
@role_required('admin')
def admin_update_homepage_content():
    identity = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    section_name = data.get('section_name')
    content = data.get('content')
    if not section_name or not content:
        return jsonify({'error': 'section_name and content are required'}), 400
    update_homepage_content(section_name, content, identity['id'])
    return jsonify({'status': 'homepage content updated'}), 200


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
