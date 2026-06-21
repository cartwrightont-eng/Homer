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
    add_university,
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
    get_accommodations_by_university,
    get_all_listings,
    get_analytics_dashboard,
    get_announcements,
    get_homepage_content,
    get_or_create_amenity,
    get_report,
    get_reports,
    get_user_by_id,
    get_universities,
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


# ==== HELPERS ====

def get_json_data(required_fields=None):
    """Get and validate JSON request data. Returns (data, error_response) tuple."""
    data = request.get_json(silent=True) or {}
    if required_fields:
        missing = [f for f in required_fields if f not in data]
        if missing:
            error_msg = f"{', '.join(missing)} {'is' if len(missing)==1 else 'are'} required"
            return None, (jsonify({'error': error_msg}), 400)
    return data, None


def check_resource_exists(resource, resource_name='resource'):
    """Check if a resource exists. Returns error response if not."""
    if not resource:
        return jsonify({'error': f'{resource_name} not found'}), 404
    return None


def check_owner(identity, resource, owner_field='owner_id', admin_role='admin'):
    """Check if user owns resource or is admin. Returns error response if not."""
    if identity.get('role') != admin_role and resource.get(owner_field) != identity.get('id'):
        return jsonify({'error': 'forbidden'}), 403
    return None


def error_response(message, status_code=400):
    """Return standard error response."""
    return jsonify({'error': message}), status_code


def success_response(message, data=None, status_code=200):
    """Return standard success response."""
    response = {'status': message}
    if data:
        response.update(data)
    return jsonify(response), status_code


def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            identity = get_jwt_identity()
            if not identity or identity.get('role') not in allowed_roles:
                return error_response('forbidden', 403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ==== AUTHENTICATION ====

@app.route('/register', methods=['POST'])
def register_user():
    data, err = get_json_data(['name', 'email', 'password', 'role'])
    if err:
        return err
    role = data['role']
    if role not in ['user', 'landlord', 'school']:
        return error_response('invalid role')
    try:
        user_id = create_user(data['name'], data['email'], data['password'], role)
    except ValueError as e:
        return error_response(str(e))
    token = create_verification_token(user_id)
    return success_response('user created', {
        'email_verification_token': token,
        'message': 'Use the token with /verify-email to complete registration',
    }, 201)


@app.route('/register-admin', methods=['POST'])
@role_required('admin')
def register_admin():
    data, err = get_json_data(['name', 'email', 'password'])
    if err:
        return err
    try:
        user_id = create_user(data['name'], data['email'], data['password'], 'admin')
    except ValueError as e:
        return error_response(str(e))
    token = create_verification_token(user_id)
    return success_response('admin user created', {'email_verification_token': token}, 201)


@app.route('/verify-email', methods=['POST'])
def verify_email():
    data, err = get_json_data(['token'])
    if err:
        return err
    if not verify_user_email(data['token']):
        return error_response('invalid or expired token')
    return success_response('email verified')


@app.route('/request-password-reset', methods=['POST'])
def request_password_reset():
    data, err = get_json_data(['email'])
    if err:
        return err
    token = create_password_reset_token(data['email'])
    if not token:
        return success_response('if the account exists, a reset link was sent')
    return success_response('password reset token created', {
        'reset_token': token,
        'message': 'Use this token with /reset-password',
    }, 200)


@app.route('/reset-password', methods=['POST'])
def reset_password_route():
    data, err = get_json_data(['token', 'password'])
    if err:
        return err
    if not reset_password(data['token'], data['password']):
        return error_response('invalid or expired token')
    return success_response('password has been reset')


@app.route('/login', methods=['POST'])
def login():
    data, err = get_json_data(['email', 'password'])
    if err:
        return err
    user = authenticate_user(data['email'], data['password'])
    if not user:
        return error_response('invalid credentials or email not verified', 401)
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
        return error_response('search query must be at least 2 characters')
    return jsonify(search_users(query))


@app.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    identity = get_jwt_identity()
    if identity['role'] != 'admin' and identity['id'] != user_id:
        return error_response('forbidden', 403)
    user = get_user_by_id(user_id)
    if not user:
        return error_response('user not found', 404)
    return jsonify(user)


@app.route('/universities', methods=['GET'])
def list_universities():
    return jsonify(get_universities())


@app.route('/universities', methods=['POST'])
@role_required('admin', 'school')
def create_university_route():
    data, err = get_json_data(['name', 'description', 'location'])
    if err:
        return err
    identity = get_jwt_identity()
    add_university(
        name=data['name'],
        description=data['description'],
        location=data['location'],
        created_by=identity['id'],
    )
    return success_response('university created', {}, 201)


@app.route('/users/<int:user_id>/suspend', methods=['POST'])
@role_required('admin')
def suspend_user_route(user_id):
    user = get_user_by_id(user_id)
    err = check_resource_exists(user, 'user')
    if err:
        return err
    suspend_user(user_id)
    return success_response('user suspended')


@app.route('/users/<int:user_id>/reactivate', methods=['POST'])
@role_required('admin')
def reactivate_user_route(user_id):
    user = get_user_by_id(user_id)
    err = check_resource_exists(user, 'user')
    if err:
        return err
    reactivate_user(user_id)
    return success_response('user reactivated')


@app.route('/users/<int:user_id>/delete', methods=['POST'])
@role_required('admin')
def delete_user_route(user_id):
    user = get_user_by_id(user_id)
    err = check_resource_exists(user, 'user')
    if err:
        return err
    delete_user(user_id)
    return success_response('user deleted')


@app.route('/users/<int:user_id>/verify-landlord', methods=['POST'])
@role_required('admin')
def verify_landlord_route(user_id):
    user = get_user_by_id(user_id)
    err = check_resource_exists(user, 'user')
    if err:
        return err
    if user['role'] != 'landlord':
        return error_response('user is not a landlord')
    verify_landlord(user_id)
    return success_response('landlord verified')


@app.route('/users/<int:user_id>/unverify-landlord', methods=['POST'])
@role_required('admin')
def unverify_landlord_route(user_id):
    user = get_user_by_id(user_id)
    err = check_resource_exists(user, 'user')
    if err:
        return err
    if user['role'] != 'landlord':
        return error_response('user is not a landlord')
    unverify_landlord(user_id)
    return success_response('landlord unverified')


# ==== ACCOMMODATIONS ====

@app.route('/accommodations', methods=['GET'])
def list_accommodations():
    is_student = request.args.get('student')
    is_student = is_student.lower() == 'true' if is_student else None
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
        return error_response('accommodation not found', 404)
    acc['amenities'] = get_accommodation_amenities(accommodation_id)
    acc['photos'] = get_accommodation_photos(accommodation_id)
    acc['videos'] = get_accommodation_videos(accommodation_id)
    return jsonify(acc)


@app.route('/my-accommodations', methods=['GET'])
@role_required('admin', 'landlord')
def my_accommodations():
    identity = get_jwt_identity()
    accs = get_accommodations_by_landlord(identity['id'])
    return jsonify(accs)


@app.route('/admin/listings', methods=['GET'])
@role_required('admin')
def admin_view_listings():
    approval_status = request.args.get('status')
    return jsonify(get_all_listings(approval_status))


@app.route('/accommodations', methods=['POST'])
@role_required('admin', 'landlord')
def create_accommodation():
    data, err = get_json_data(['name', 'description', 'price', 'location', 'availability_option'])
    if err:
        return err
    if data['availability_option'] not in ['buy', 'rent', 'both']:
        return error_response('availability_option must be buy, rent, or both')
    identity = get_jwt_identity()
    acc_id = add_accommodation(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        location=data['location'],
        university_id=data.get('university_id'),
        owner_id=identity['id'],
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        distance_km=data.get('distance_km'),
        availability_option=data['availability_option'],
        vacancy_status=data.get('vacancy_status', 'vacant'),
        units_available=data.get('units_available', 1),
        is_student_accommodation=data.get('is_student_accommodation', False),
        is_university_owned=data.get('is_university_owned', False),
    )
    return success_response('accommodation created', {'id': acc_id}, 201)


@app.route('/accommodations/<int:accommodation_id>', methods=['PUT'])
@jwt_required()
def update_accommodation_route(accommodation_id):
    identity = get_jwt_identity()
    acc = get_accommodation(accommodation_id)
    err = check_resource_exists(acc)
    if err:
        return err
    err = check_owner(identity, acc)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    update_accommodation(accommodation_id, **data)
    return success_response('accommodation updated')


@app.route('/admin/listings/<int:listing_id>/approve', methods=['POST'])
@role_required('admin')
def admin_approve_listing(listing_id):
    acc = get_accommodation(listing_id)
    err = check_resource_exists(acc, 'listing')
    if err:
        return err
    approve_listing(listing_id)
    return success_response('listing approved')


@app.route('/admin/listings/<int:listing_id>/reject', methods=['POST'])
@role_required('admin')
def admin_reject_listing(listing_id):
    data, err = get_json_data()
    if err:
        return err
    acc = get_accommodation(listing_id)
    err = check_resource_exists(acc, 'listing')
    if err:
        return err
    reason = data.get('reason', 'No reason provided')
    reject_listing(listing_id, reason)
    return success_response('listing rejected')


@app.route('/admin/listings/<int:listing_id>/mark-suspicious', methods=['POST'])
@role_required('admin')
def admin_mark_suspicious(listing_id):
    data, err = get_json_data()
    if err:
        return err
    acc = get_accommodation(listing_id)
    err = check_resource_exists(acc, 'listing')
    if err:
        return err
    reason = data.get('reason', 'Suspicious activity detected')
    mark_listing_suspicious(listing_id, reason)
    return success_response('listing marked suspicious')


@app.route('/admin/listings/<int:listing_id>/unmark-suspicious', methods=['POST'])
@role_required('admin')
def admin_unmark_suspicious(listing_id):
    acc = get_accommodation(listing_id)
    err = check_resource_exists(acc, 'listing')
    if err:
        return err
    unmark_listing_suspicious(listing_id)
    return success_response('listing unmarked suspicious')


@app.route('/admin/listings/<int:listing_id>/edit', methods=['PUT'])
@role_required('admin')
def admin_edit_listing(listing_id):
    acc = get_accommodation(listing_id)
    err = check_resource_exists(acc, 'listing')
    if err:
        return err
    data = request.get_json(silent=True) or {}
    edit_listing(listing_id, **data)
    return success_response('listing updated')


# ==== PHOTOS ====

@app.route('/accommodations/<int:accommodation_id>/photos', methods=['POST'])
@jwt_required()
def upload_photo(accommodation_id):
    identity = get_jwt_identity()
    acc = get_accommodation(accommodation_id)
    err = check_resource_exists(acc, 'accommodation')
    if err:
        return err
    err = check_owner(identity, acc)
    if err:
        return err
    data, err = get_json_data(['photo_url'])
    if err:
        return err
    photo_id = add_accommodation_photo(accommodation_id, data['photo_url'], data.get('description'))
    return success_response('photo uploaded', {'id': photo_id}, 201)


@app.route('/accommodations/<int:accommodation_id>/photos', methods=['GET'])
def get_photos(accommodation_id):
    return jsonify(get_accommodation_photos(accommodation_id))


@app.route('/accommodations/<int:accommodation_id>/videos', methods=['POST'])
@jwt_required()
def upload_video(accommodation_id):
    identity = get_jwt_identity()
    acc = get_accommodation(accommodation_id)
    err = check_resource_exists(acc, 'accommodation')
    if err:
        return err
    err = check_owner(identity, acc)
    if err:
        return err
    data, err = get_json_data(['video_url'])
    if err:
        return err
    video_id = add_accommodation_video(accommodation_id, data['video_url'], data.get('title'))
    return success_response('video uploaded', {'id': video_id}, 201)


@app.route('/accommodations/<int:accommodation_id>/videos', methods=['GET'])
def get_videos(accommodation_id):
    return jsonify(get_accommodation_videos(accommodation_id))


@app.route('/accommodations/<int:accommodation_id>/amenities', methods=['POST'])
@jwt_required()
def add_amenity_to_accommodation(accommodation_id):
    identity = get_jwt_identity()
    acc = get_accommodation(accommodation_id)
    err = check_resource_exists(acc, 'accommodation')
    if err:
        return err
    err = check_owner(identity, acc)
    if err:
        return err
    data, err = get_json_data(['name', 'category'])
    if err:
        return err
    if data['category'] not in ['mall', 'restaurant', 'other']:
        return error_response('category must be mall, restaurant, or other')
    amenity_id = get_or_create_amenity(data['name'], data['category'])
    add_accommodation_amenity(accommodation_id, amenity_id, data.get('distance_km'))
    return success_response('amenity added', {'amenity_id': amenity_id}, 201)


@app.route('/accommodations/<int:accommodation_id>/amenities', methods=['GET'])
def get_amenities(accommodation_id):
    return jsonify(get_accommodation_amenities(accommodation_id))


# ==== REPORTS ====

@app.route('/reports', methods=['POST'])
@jwt_required()
def create_report_route():
    identity = get_jwt_identity()
    data, err = get_json_data(['report_type', 'reason'])
    if err:
        return err
    report_id = create_report(
        report_type=data['report_type'],
        reason=data['reason'],
        description=data.get('description'),
        reporter_id=identity['id'],
        reported_user_id=data.get('reported_user_id'),
        reported_accommodation_id=data.get('reported_accommodation_id'),
    )
    return success_response('report created', {'id': report_id}, 201)


@app.route('/admin/reports', methods=['GET'])
@role_required('admin')
def admin_view_reports():
    status = request.args.get('status')
    return jsonify(get_reports(status))


@app.route('/admin/reports/<int:report_id>', methods=['GET'])
@role_required('admin')
def admin_get_report(report_id):
    report = get_report(report_id)
    err = check_resource_exists(report, 'report')
    if err:
        return err
    return jsonify(report)


@app.route('/admin/reports/<int:report_id>/resolve', methods=['POST'])
@role_required('admin')
def admin_resolve_report(report_id):
    report = get_report(report_id)
    err = check_resource_exists(report, 'report')
    if err:
        return err
    data, err = get_json_data()
    if err:
        return err
    resolution_notes = data.get('resolution_notes', '')
    resolve_report(report_id, resolution_notes)
    return success_response('report resolved')


@app.route('/announcements', methods=['GET'])
def get_announcements_route():
    announcement_type = request.args.get('type')
    return jsonify(get_announcements(announcement_type))


@app.route('/admin/announcements', methods=['POST'])
@role_required('admin')
def admin_create_announcement():
    identity = get_jwt_identity()
    data, err = get_json_data(['title', 'content', 'announcement_type'])
    if err:
        return err
    if data['announcement_type'] not in ['alert', 'maintenance', 'notice']:
        return error_response('invalid announcement_type')
    announcement_id = create_announcement(
        title=data['title'],
        content=data['content'],
        announcement_type=data['announcement_type'],
        created_by=identity['id']
    )
    return success_response('announcement created', {'id': announcement_id}, 201)


@app.route('/admin/announcements/<int:announcement_id>/deactivate', methods=['POST'])
@role_required('admin')
def admin_deactivate_announcement(announcement_id):
    deactivate_announcement(announcement_id)
    return success_response('announcement deactivated')


@app.route('/homepage/content', methods=['GET'])
def get_homepage_content_route():
    section = request.args.get('section')
    return jsonify(get_homepage_content(section))


@app.route('/admin/homepage/content', methods=['POST'])
@role_required('admin')
def admin_update_homepage_content():
    identity = get_jwt_identity()
    data, err = get_json_data(['section_name', 'content'])
    if err:
        return err
    update_homepage_content(data['section_name'], data['content'], identity['id'])
    return success_response('homepage content updated')


@app.route('/admin/analytics', methods=['GET'])
@role_required('admin')
def admin_analytics():
    return jsonify(get_analytics_dashboard())


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
