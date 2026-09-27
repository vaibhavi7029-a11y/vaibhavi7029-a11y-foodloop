from flask import Flask, render_template, request, redirect, session
import mysql.connector
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config.from_object(Config)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    return mysql.connector.connect(
        host=app.config["MYSQL_HOST"],
        user=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        database=app.config["MYSQL_DATABASE"]
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return "FoodLoop is Running!"


# =========================================================
# DATABASE TEST
# =========================================================

@app.route("/db-test")
def db_test():

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        if result:
            return "MySQL Database Connected Successfully!"

    except Exception as e:
        return f"Database Error: {e}"


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        phone = request.form.get("phone")

        organization_name = request.form.get(
            "organization_name"
        )

        address = request.form.get("address")
        city = request.form.get("city")

        hashed_password = generate_password_hash(
            password
        )

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            cursor.execute("""
                INSERT INTO users
                (
                    name,
                    email,
                    password,
                    role,
                    phone
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                name,
                email,
                hashed_password,
                role,
                phone
            ))

            user_id = cursor.lastrowid

            if role in ["RESTAURANT", "NGO"]:

                organization_type = role

                cursor.execute("""
                    INSERT INTO organizations
                    (
                        name,
                        organization_type,
                        owner_user_id,
                        phone,
                        email,
                        address,
                        city
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                """, (
                    organization_name,
                    organization_type,
                    user_id,
                    phone,
                    email,
                    address,
                    city
                ))

                organization_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO subscriptions
                    (
                        organization_id,
                        plan,
                        status
                    )
                    VALUES
                    (
                        %s,
                        'FREE',
                        'ACTIVE'
                    )
                """, (
                    organization_id,
                ))

            connection.commit()

            cursor.close()
            connection.close()

            return redirect("/login")

        except mysql.connector.Error as e:

            connection.rollback()

            cursor.close()
            connection.close()

            return f"Registration Error: {e}"

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute("""
            SELECT *
            FROM users
            WHERE email = %s
        """, (
            email,
        ))

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["user_id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            if user["role"] == "ADMIN":
                return redirect("/admin")

            return redirect("/dashboard")

        return "Invalid email or password"

    return render_template(
        "login.html"
    )


# =========================================================
# NORMAL DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] == "ADMIN":
        return redirect("/admin")

    return render_template(
        "dashboard.html"
    )


# =========================================================
# ADMIN MAIN PAGE - ALL DATA
# =========================================================

@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "ADMIN":
        return "Access Denied"

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    # =====================================================
    # ALL USERS
    # =====================================================

    cursor.execute("""
        SELECT
            user_id,
            name,
            email,
            role,
            phone,
            created_at
        FROM users
        ORDER BY created_at DESC
    """)

    users = cursor.fetchall()


    # =====================================================
    # RESTAURANTS
    # =====================================================

    cursor.execute("""
        SELECT
            u.user_id,
            u.name,
            u.email,
            u.phone,
            u.created_at,

            o.organization_id,
            o.name AS organization_name,
            o.address,
            o.city

        FROM users u

        LEFT JOIN organizations o
        ON u.user_id = o.owner_user_id

        WHERE u.role = 'RESTAURANT'

        ORDER BY u.created_at DESC
    """)

    restaurants = cursor.fetchall()


    # =====================================================
    # NGOs
    # =====================================================

    cursor.execute("""
        SELECT
            u.user_id,
            u.name,
            u.email,
            u.phone,
            u.created_at,

            o.organization_id,
            o.name AS organization_name,
            o.address,
            o.city

        FROM users u

        LEFT JOIN organizations o
        ON u.user_id = o.owner_user_id

        WHERE u.role = 'NGO'

        ORDER BY u.created_at DESC
    """)

    ngos = cursor.fetchall()


    # =====================================================
    # VOLUNTEERS
    # =====================================================

    cursor.execute("""
        SELECT
            user_id,
            name,
            email,
            phone,
            created_at

        FROM users

        WHERE role = 'VOLUNTEER'

        ORDER BY created_at DESC
    """)

    volunteers = cursor.fetchall()


    # =====================================================
    # ALL FOOD DONATIONS
    # =====================================================

    cursor.execute("""
        SELECT

            d.donation_id,
            d.food_name,
            d.food_type,
            d.quantity,
            d.quantity_unit,
            d.preparation_time,
            d.available_until,
            d.description,
            d.status,
            d.created_at,

            o.name AS restaurant_name,
            o.city AS restaurant_city

        FROM food_donations d

        JOIN organizations o
        ON d.organization_id =
           o.organization_id

        ORDER BY d.created_at DESC
    """)

    donations = cursor.fetchall()


    # =====================================================
    # ALL FOOD REQUESTS
    # =====================================================

    cursor.execute("""
        SELECT

            r.request_id,
            r.requested_quantity,
            r.status,
            r.requested_at,

            d.food_name,
            d.food_type,
            d.quantity,
            d.quantity_unit,

            restaurant.name AS restaurant_name,

            ngo.name AS ngo_name,
            ngo.city AS ngo_city

        FROM food_requests r

        JOIN food_donations d
        ON r.donation_id =
           d.donation_id

        JOIN organizations restaurant
        ON d.organization_id =
           restaurant.organization_id

        JOIN organizations ngo
        ON r.ngo_organization_id =
           ngo.organization_id

        ORDER BY r.requested_at DESC
    """)

    food_requests = cursor.fetchall()


    # =====================================================
    # ALL PICKUPS / DELIVERIES
    # =====================================================

    cursor.execute("""
        SELECT

            p.pickup_id,
            p.request_id,
            p.pickup_time,
            p.delivery_time,
            p.status,
            p.notes,

            volunteer.name AS volunteer_name,
            volunteer.phone AS volunteer_phone,

            d.food_name,
            d.quantity,
            d.quantity_unit,

            restaurant.name AS restaurant_name,

            ngo.name AS ngo_name

        FROM pickups p

        JOIN food_requests r
        ON p.request_id =
           r.request_id

        JOIN food_donations d
        ON r.donation_id =
           d.donation_id

        JOIN organizations restaurant
        ON d.organization_id =
           restaurant.organization_id

        JOIN organizations ngo
        ON r.ngo_organization_id =
           ngo.organization_id

        LEFT JOIN users volunteer
        ON p.volunteer_user_id =
           volunteer.user_id

        ORDER BY p.pickup_id DESC
    """)

    pickups = cursor.fetchall()


    # =====================================================
    # ALL FEEDBACK
    # =====================================================

    cursor.execute("""
        SELECT

            f.feedback_id,
            f.rating,
            f.comment,
            f.created_at,

            u.name AS user_name,
            u.email AS user_email,

            r.request_id

        FROM feedback f

        JOIN users u
        ON f.user_id =
           u.user_id

        JOIN food_requests r
        ON f.request_id =
           r.request_id

        ORDER BY f.created_at DESC
    """)

    feedback = cursor.fetchall()


    # =====================================================
    # ALL SUBSCRIPTIONS
    # =====================================================

    cursor.execute("""
        SELECT

            s.subscription_id,
            s.plan,
            s.start_date,
            s.end_date,
            s.status,

            o.name AS organization_name,
            o.organization_type

        FROM subscriptions s

        JOIN organizations o
        ON s.organization_id =
           o.organization_id

        ORDER BY s.subscription_id DESC
    """)

    subscriptions = cursor.fetchall()


    # =====================================================
    # COUNTS
    # =====================================================

    total_users = len(users)
    total_restaurants = len(restaurants)
    total_ngos = len(ngos)
    total_volunteers = len(volunteers)

    total_donations = len(donations)
    total_requests = len(food_requests)
    total_pickups = len(pickups)
    total_feedback = len(feedback)
    total_subscriptions = len(subscriptions)


    # =====================================================
    # CLOSE DATABASE
    # =====================================================

    cursor.close()
    connection.close()


    # =====================================================
    # SEND DATA TO ADMIN.HTML
    # =====================================================

    return render_template(
        "admin.html",

        users=users,

        restaurants=restaurants,

        ngos=ngos,

        volunteers=volunteers,

        donations=donations,

        food_requests=food_requests,

        pickups=pickups,

        feedback=feedback,

        subscriptions=subscriptions,

        total_users=total_users,

        total_restaurants=total_restaurants,

        total_ngos=total_ngos,

        total_volunteers=total_volunteers,

        total_donations=total_donations,

        total_requests=total_requests,

        total_pickups=total_pickups,

        total_feedback=total_feedback,

        total_subscriptions=total_subscriptions
    )


# =========================================================
# ADD SURPLUS FOOD
# =========================================================

@app.route(
    "/add-donation",
    methods=["GET", "POST"]
)
def add_donation():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "RESTAURANT":
        return "Access Denied"

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT *
        FROM organizations
        WHERE owner_user_id = %s
        AND organization_type = 'RESTAURANT'
    """, (
        session["user_id"],
    ))

    organization = cursor.fetchone()

    if not organization:

        cursor.close()
        connection.close()

        return "Restaurant organization not found"

    if request.method == "POST":

        food_name = request.form[
            "food_name"
        ]

        food_type = request.form[
            "food_type"
        ]

        quantity = request.form[
            "quantity"
        ]

        quantity_unit = request.form[
            "quantity_unit"
        ]

        preparation_time = request.form.get(
            "preparation_time"
        )

        available_until = request.form.get(
            "available_until"
        )

        description = request.form.get(
            "description"
        )

        cursor.execute("""
            INSERT INTO food_donations
            (
                organization_id,
                food_name,
                food_type,
                quantity,
                quantity_unit,
                preparation_time,
                available_until,
                description,
                status
            )

            VALUES
            (
                %s, %s, %s, %s, %s,
                %s, %s, %s, 'AVAILABLE'
            )
        """, (
            organization["organization_id"],
            food_name,
            food_type,
            quantity,
            quantity_unit,
            preparation_time,
            available_until,
            description
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect("/donations")

    cursor.close()
    connection.close()

    return render_template(
        "add_donation.html"
    )


# =========================================================
# MY DONATIONS - RESTAURANT
# =========================================================

@app.route("/donations")
def donations():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "RESTAURANT":
        return "Access Denied"

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT d.*

        FROM food_donations d

        JOIN organizations o
        ON d.organization_id =
           o.organization_id

        WHERE o.owner_user_id = %s

        ORDER BY d.created_at DESC
    """, (
        session["user_id"],
    ))

    donations = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "donations.html",
        donations=donations
    )


# =========================================================
# AVAILABLE FOOD - NGO
# =========================================================

@app.route("/available-food")
def available_food():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "NGO":
        return "Access Denied"

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT
            d.*,
            o.name AS donor_name

        FROM food_donations d

        JOIN organizations o
        ON d.organization_id =
           o.organization_id

        WHERE d.status = 'AVAILABLE'

        ORDER BY d.created_at DESC
    """)

    foods = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "available_food.html",
        foods=foods
    )


# =========================================================
# REQUEST FOOD - NGO
# =========================================================

@app.route(
    "/request-food/<int:donation_id>",
    methods=["GET", "POST"]
)
def request_food(donation_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "NGO":
        return "Access Denied"

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT
            d.*,
            o.name AS donor_name

        FROM food_donations d

        JOIN organizations o
        ON d.organization_id =
           o.organization_id

        WHERE d.donation_id = %s

        AND d.status = 'AVAILABLE'
    """, (
        donation_id,
    ))

    donation = cursor.fetchone()

    if not donation:

        cursor.close()
        connection.close()

        return "Food donation not available"

    cursor.execute("""
        SELECT *
        FROM organizations

        WHERE owner_user_id = %s

        AND organization_type = 'NGO'
    """, (
        session["user_id"],
    ))

    ngo = cursor.fetchone()

    if not ngo:

        cursor.close()
        connection.close()

        return "NGO organization not found"

    if request.method == "POST":

        requested_quantity = int(
            request.form[
                "requested_quantity"
            ]
        )

        if requested_quantity <= 0:

            cursor.close()
            connection.close()

            return "Invalid quantity"

        if requested_quantity > donation["quantity"]:

            cursor.close()
            connection.close()

            return (
                "Requested quantity "
                "exceeds available quantity"
            )

        cursor.execute("""
            INSERT INTO food_requests
            (
                donation_id,
                ngo_organization_id,
                requested_quantity,
                status
            )

            VALUES
            (
                %s, %s, %s, 'PENDING'
            )
        """, (
            donation_id,
            ngo["organization_id"],
            requested_quantity
        ))

        cursor.execute("""
            UPDATE food_donations

            SET status = 'REQUESTED'

            WHERE donation_id = %s
        """, (
            donation_id,
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            "/my-requests"
        )

    cursor.close()
    connection.close()

    return render_template(
        "request.html",
        donation=donation
    )


# =========================================================
# NGO MY REQUESTS
# =========================================================

@app.route("/my-requests")
def my_requests():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "NGO":
        return "Access Denied"

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT
            r.*,

            d.food_name,
            d.food_type,
            d.quantity,
            d.quantity_unit,

            donor.name AS donor_name,
            donor.phone AS donor_phone,
            donor.email AS donor_email

        FROM food_requests r

        JOIN food_donations d
        ON r.donation_id =
           d.donation_id

        JOIN organizations donor_org
        ON d.organization_id =
           donor_org.organization_id

        JOIN users donor
        ON donor_org.owner_user_id =
           donor.user_id

        JOIN organizations ngo_org
        ON r.ngo_organization_id =
           ngo_org.organization_id

        WHERE ngo_org.owner_user_id = %s

        ORDER BY r.requested_at DESC
    """, (
        session["user_id"],
    ))

    requests = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "requests.html",
        requests=requests
    )


# =========================================================
# RESTAURANT FOOD REQUESTS
# =========================================================

@app.route("/food-requests")
def food_requests():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "RESTAURANT":
        return "Access Denied"

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT

            r.request_id,
            r.requested_quantity,
            r.status,
            r.requested_at,

            d.food_name,
            d.food_type,
            d.quantity,
            d.quantity_unit,

            ngo.name AS ngo_name,
            ngo.phone AS ngo_phone,
            ngo.email AS ngo_email

        FROM food_requests r

        JOIN food_donations d
        ON r.donation_id =
           d.donation_id

        JOIN organizations restaurant
        ON d.organization_id =
           restaurant.organization_id

        JOIN organizations ngo
        ON r.ngo_organization_id =
           ngo.organization_id

        WHERE restaurant.owner_user_id = %s

        ORDER BY r.requested_at DESC
    """, (
        session["user_id"],
    ))

    requests = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "food_requests.html",
        requests=requests
    )


# =========================================================
# APPROVE / REJECT FOOD REQUEST
# =========================================================

@app.route(
    "/update-request/<int:request_id>/<action>"
)
def update_request(request_id, action):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "RESTAURANT":
        return "Access Denied"

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT
            r.*,
            d.organization_id AS restaurant_id

        FROM food_requests r

        JOIN food_donations d
        ON r.donation_id =
           d.donation_id

        JOIN organizations o
        ON d.organization_id =
           o.organization_id

        WHERE r.request_id = %s

        AND o.owner_user_id = %s
    """, (
        request_id,
        session["user_id"]
    ))

    food_request = cursor.fetchone()

    if not food_request:

        cursor.close()
        connection.close()

        return "Request not found"

    if action == "approve":

        if food_request["status"] != "PENDING":

            cursor.close()
            connection.close()

            return "Invalid request status"

        cursor.execute("""
            UPDATE food_requests

            SET status = 'APPROVED'

            WHERE request_id = %s
        """, (
            request_id,
        ))

        connection.commit()

    elif action == "reject":

        if food_request["status"] != "PENDING":

            cursor.close()
            connection.close()

            return "Invalid request status"

        cursor.execute("""
            UPDATE food_requests

            SET status = 'REJECTED'

            WHERE request_id = %s
        """, (
            request_id,
        ))

        cursor.execute("""
            UPDATE food_donations

            SET status = 'AVAILABLE'

            WHERE donation_id = %s
        """, (
            food_request["donation_id"],
        ))

        connection.commit()

    else:

        cursor.close()
        connection.close()

        return "Invalid action"

    cursor.close()
    connection.close()

    return redirect(
        "/food-requests"
    )


# =========================================================
# ASSIGN VOLUNTEER
# =========================================================

@app.route(
    "/assign-volunteer/<int:request_id>",
    methods=["GET", "POST"]
)
def assign_volunteer(request_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "RESTAURANT":
        return "Access Denied"

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT
            r.*,

            d.food_name,
            d.food_type,

            ngo.name AS ngo_name,
            ngo.phone AS ngo_phone,
            ngo.address AS ngo_address

        FROM food_requests r

        JOIN food_donations d
        ON r.donation_id =
           d.donation_id

        JOIN organizations restaurant
        ON d.organization_id =
           restaurant.organization_id

        JOIN organizations ngo
        ON r.ngo_organization_id =
           ngo.organization_id

        WHERE r.request_id = %s

        AND restaurant.owner_user_id = %s
    """, (
        request_id,
        session["user_id"]
    ))

    food_request = cursor.fetchone()

    if not food_request:

        cursor.close()
        connection.close()

        return "Request not found"

    if food_request["status"] != "APPROVED":

        cursor.close()
        connection.close()

        return (
            "Volunteer can only be "
            "assigned to approved requests"
        )

    cursor.execute("""
        SELECT *
        FROM pickups
        WHERE request_id = %s
    """, (
        request_id,
    ))

    existing_pickup = cursor.fetchone()

    if existing_pickup:

        cursor.close()
        connection.close()

        return "Volunteer already assigned"

    cursor.execute("""
        SELECT
            user_id,
            name,
            email,
            phone

        FROM users

        WHERE role = 'VOLUNTEER'

        ORDER BY name
    """)

    volunteers = cursor.fetchall()

    if request.method == "POST":

        volunteer_user_id = request.form[
            "volunteer_user_id"
        ]

        pickup_time = request.form.get(
            "pickup_time"
        )

        notes = request.form.get(
            "notes"
        )

        cursor.execute("""
            INSERT INTO pickups
            (
                request_id,
                volunteer_user_id,
                pickup_time,
                status,
                notes
            )

            VALUES
            (
                %s, %s, %s, 'ASSIGNED', %s
            )
        """, (
            request_id,
            volunteer_user_id,
            pickup_time,
            notes
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            "/food-requests"
        )

    cursor.close()
    connection.close()

    return render_template(
        "assign_volunteer.html",
        request=food_request,
        volunteers=volunteers
    )


# =========================================================
# VOLUNTEER MY PICKUPS
# =========================================================

@app.route("/pickups")
def pickups():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "VOLUNTEER":
        return "Access Denied"

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT

            p.pickup_id,
            p.request_id,
            p.volunteer_user_id,
            p.pickup_time,
            p.delivery_time,
            p.status AS pickup_status,
            p.notes,

            r.requested_quantity,

            d.food_name,
            d.food_type,
            d.quantity,
            d.quantity_unit,

            donor.name AS donor_name,
            donor.phone AS donor_phone,

            ngo.name AS ngo_name,
            ngo.phone AS ngo_phone,
            ngo.address AS ngo_address

        FROM pickups p

        JOIN food_requests r
        ON p.request_id =
           r.request_id

        JOIN food_donations d
        ON r.donation_id =
           d.donation_id

        JOIN organizations donor_org
        ON d.organization_id =
           donor_org.organization_id

        JOIN users donor
        ON donor_org.owner_user_id =
           donor.user_id

        JOIN organizations ngo
        ON r.ngo_organization_id =
           ngo.organization_id

        WHERE p.volunteer_user_id = %s

        ORDER BY p.pickup_time DESC
    """, (
        session["user_id"],
    ))

    pickups = cursor.fetchall()

    for pickup in pickups:

        pickup["status"] = pickup[
            "pickup_status"
        ]

    cursor.close()
    connection.close()

    return render_template(
        "pickups.html",
        pickups=pickups
    )


# =========================================================
# UPDATE PICKUP STATUS - VOLUNTEER
# =========================================================

@app.route(
    "/update-pickup/<int:pickup_id>/<action>"
)
def update_pickup(pickup_id, action):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "VOLUNTEER":
        return "Access Denied"

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT *
        FROM pickups

        WHERE pickup_id = %s

        AND volunteer_user_id = %s
    """, (
        pickup_id,
        session["user_id"]
    ))

    pickup = cursor.fetchone()

    if not pickup:

        cursor.close()
        connection.close()

        return "Pickup not found"

    current_status = pickup[
        "status"
    ]

    if action == "start":

        if current_status != "ASSIGNED":

            cursor.close()
            connection.close()

            return "Invalid pickup status"

        new_status = "ON_THE_WAY"

    elif action == "collect":

        if current_status != "ON_THE_WAY":

            cursor.close()
            connection.close()

            return "Invalid pickup status"

        new_status = "COLLECTED"

    elif action == "deliver":

        if current_status != "COLLECTED":

            cursor.close()
            connection.close()

            return "Invalid pickup status"

        new_status = "DELIVERED"

    else:

        cursor.close()
        connection.close()

        return "Invalid action"

    if new_status == "DELIVERED":

        cursor.execute("""
            UPDATE pickups

            SET
                status = %s,
                delivery_time = NOW()

            WHERE pickup_id = %s
        """, (
            new_status,
            pickup_id
        ))

        cursor.execute("""
            UPDATE food_requests

            SET status = 'COMPLETED'

            WHERE request_id = %s
        """, (
            pickup["request_id"],
        ))

        cursor.execute("""
            UPDATE food_donations d

            JOIN food_requests r
            ON d.donation_id =
               r.donation_id

            SET d.status = 'COMPLETED'

            WHERE r.request_id = %s
        """, (
            pickup["request_id"],
        ))

    else:

        cursor.execute("""
            UPDATE pickups

            SET status = %s

            WHERE pickup_id = %s
        """, (
            new_status,
            pickup_id
        ))

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(
        "/pickups"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)