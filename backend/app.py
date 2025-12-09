import os
import psycopg2
import psycopg2.extras
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

def get_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn

app = Flask(__name__)


@app.get("/subjects")
def subjects_list():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT * FROM subjects ORDER BY name ASC")
    rows = cur.fetchall()

    cur.close()
    conn.close()
    return jsonify(rows)


@app.get("/subjects/<int:sid>")
def subjects_get(sid):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT * FROM subjects WHERE id = %s", (sid,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify(row)



@app.post("/subjects")
def subjects_create():
    data = request.get_json()
    
    if not data or "name" not in data:
        return jsonify({"error": "missing field 'name'"}), 400
    
    name = data.get("name")
    description = data.get("description", "")
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Проверяем, существует ли уже предмет с таким названием
        cur.execute("SELECT id FROM subjects WHERE name ILIKE %s", (name,))
        existing = cur.fetchone()
        
        if existing:
            return jsonify({"error": "subject with this name already exists"}), 409
        
        # Создаем новый предмет
        cur.execute(
            "INSERT INTO subjects (name, description) VALUES (%s, %s) RETURNING *",
            (name, description)
        )
        
        new_subject = cur.fetchone()
        conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify(new_subject), 201
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.get("/subjects/by_name")
def subjects_get_by_name():
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "missing parameter 'name'"}), 400

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT * FROM subjects WHERE name ILIKE %s", (f"%{name}%",))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    if not rows:
        return jsonify({"error": "not found"}), 404

    return jsonify(rows)

@app.get("/services")
def services_list():

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    offset = (page - 1) * per_page

    subject_id = request.args.get("subject_id")
    subject_name = request.args.get("subject_name")
    q = request.args.get("q")

    filters = []
    params = []

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if subject_name:
        cur.execute("SELECT id FROM subjects WHERE name ILIKE %s", (f"%{subject_name}%",))
        results = cur.fetchall()
        if results:
            ids = [r["id"] for r in results]
            filters.append(f"subject_id IN %s")
            params.append(tuple(ids))
        else:
            return jsonify({
                "items": [],
                "page": page,
                "per_page": per_page,
                "total": 0,
                "pages": 0
            })

    elif subject_id:
        filters.append("subject_id = %s")
        params.append(subject_id)

    if q:
        filters.append("title ILIKE %s")
        params.append(f"%{q}%")

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""

    sql = f"""
        SELECT * FROM advertisements
        {where_clause}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """
    cur.execute(sql, params + [per_page, offset])
    items = cur.fetchall()

    count_sql = f"SELECT COUNT(*) FROM advertisements {where_clause}"
    cur.execute(count_sql, params)
    total = cur.fetchone()["count"]

    cur.close()
    conn.close()

    return jsonify({
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total + per_page - 1) // per_page
    })



@app.get("/services/<int:ad_id>")
def services_get(ad_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT * FROM advertisements WHERE id = %s", (ad_id,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "not found"}), 404

    return jsonify(row)


@app.post("/services")
def services_create():
    data = request.get_json()

    req_fields = ["title", "description", "contact_info", "subject_id"]
    missing = [f for f in req_fields if f not in data]
    if missing:
        return jsonify({"error": f"missing fields: {missing}"}), 400

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    sql = """
        INSERT INTO advertisements 
        (title, description, price, education_format, contact_info, subject_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING *
    """

    cur.execute(sql, (
        data["title"],
        data["description"],
        data.get("price"),
        data.get("education_format"),
        data["contact_info"],
        data["subject_id"],
    ))

    new_item = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    return jsonify(new_item), 201

@app.post("/services/bulk_import")
def services_bulk():
    json_data = request.get_json()
    if not json_data or "services" not in json_data:
        return jsonify({"error": "expected { services: [...] }"}), 400

    services = json_data["services"]

    conn = get_db()
    cur = conn.cursor()

    success = 0
    errors = []

    for idx, s in enumerate(services):
        try:
            cur.execute("""
                INSERT INTO advertisements
                (id, title, description, price, education_format, contact_info, subject_id, created_at, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO NOTHING
            """, (
                s["id"],
                s["title"],
                s["description"],
                s["price"],
                s.get("education_format"),
                s["contact_info"],
                s["subject_id"],
                s.get("created_at"),
                s.get("updated_at")
            ))
            success += 1
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})
            conn.rollback()

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"imported": success, "errors": errors}), 201


@app.get("/")
def index():
    return jsonify({"status": "ok", "routes": ["/services", "/subjects"]})


if __name__ == "__main__":
    app.run(debug=True)
