import os, cv2
import sqlite3
import gpxpy
import gpxpy.gpx
from math import radians, sin, cos, sqrt, atan2


def connect_to_database(db_path='db/rdd.sqlite'):
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Mengembalikan hasil query sebagai dict-like objek
        print("Koneksi database berhasil.")
        return conn
    except sqlite3.Error as e:
        print(f"Error saat menghubungkan ke database: {e}")
        return False


def create_inspection_folder(inspection_id, location, time):
    base_path = os.path.join(os.getcwd(), 'assets/inspections')  # Path ke folder assets
    folder_name = inspection_id + "_" + location + "_" + time
    folder_path = os.path.join(base_path, folder_name)

    try:
        os.makedirs(folder_path, exist_ok=True)
        print(f"Folder '{folder_name}' berhasil dibuat di '{folder_path}'")

        return folder_name
    except Exception as e:
        print(f"Gagal membuat folder: {e}")
    return False


def displacement(lat1, lon1, lat2, lon2):
    # Radius bumi dalam meter
    r = 6371000  # meter

    # Konversi derajat ke radian
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    # Perbedaan koordinat
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Menghitung jarak
    return r * c


def save_cracks(inspection_id, cracks):
    status = False
    conn = connect_to_database()
    if conn:
        cursor = conn.cursor()
        columns = "inspection_id, image, damage_type, coordinat"
        values = []
        # Validasi apakah cracks memiliki data
        if not cracks:
            print("No cracks data provided.")
            return False
        for crack in cracks:
            try:
                val = (
                    inspection_id,
                    crack['image'],
                    crack['type'],  # Contoh: 0 = longitudinal, 1 = alligator, dst.
                    "{0},{1}".format(crack['coordinat'][0], crack['coordinat'][1]),
                )
                values.append(val)
            except KeyError as ke:
                print(f"Data error: {ke}. Skipping this crack.")
        query = f'INSERT INTO Detections ({columns}) VALUES (?, ?, ?, ?)'
        print("Executing batch insert with query: ", query)
        print("Executing batch insert with values : ", values)
        try:
            cursor.executemany(query, values)
            conn.commit()
            if cursor.rowcount > 0:
                status = True
        except Exception as e:
            print("Database error:", e)  # Tambahkan log error
            conn.rollback()  # Rollback jika terjadi kesalahan
        finally:
            conn.close()
    return status


def get_cracks(inspection_id, coordinat):
    conn = connect_to_database()
    if conn:
        cursor = conn.cursor()
        query = "SELECT damage_type " \
                "FROM Detections " \
                "WHERE inspection_id = {0} " \
                "AND coordinat = '{1}' ".format(inspection_id, coordinat)
        cursor.execute(query)
        row = cursor.fetchone()
        if row is None:
            cursor.close()
            return False
        inspection = dict(row)
        print(inspection)
        return inspection
    else:
        return False


def update_cracks(inspection_id, new_cracks, coordinat):
    status = False
    conn = connect_to_database()
    if conn:
        cursor = conn.cursor()
        old_cracks = get_cracks(inspection_id, coordinat)
        latest_cracks = old_cracks["damage_type"] + "," + new_cracks
        query = 'UPDATE Detections ' \
                'SET damage_type = "{0}" ' \
                'WHERE inspection_id = {1} ' \
                'AND coordinat = "{2}"'.format(latest_cracks, inspection_id, coordinat)
        try:
            cursor.execute(query)
            conn.commit()
            detection_id = cursor.rowcount
            status = status if detection_id == 0 else {detection_id}
        except Exception as e:
            conn.rollback()  # Rollback jika terjadi kesalahan
        finally:
            conn.close()
    return status


def update_inspections(inspection_id, data):
    status = False
    conn = connect_to_database()
    print("Data untuk update:", data)
    if conn:
        cursor = conn.cursor()

        # Mempersiapkan query dengan binding parameter untuk menghindari SQL injection
        query = """
                UPDATE Inspections
                SET count_crack = count_crack + ?,
                    count_longitudinal_cracks = count_longitudinal_cracks + ?,
                    count_transverse_cracks = count_transverse_cracks + ?,
                    count_alligator_cracks = count_alligator_cracks + ?,
                    count_potholes = count_potholes + ?
                WHERE id = ?
            """

        # Mengatur nilai yang akan ditambahkan
        values = (
            data.get('count_crack', 0),
            data.get('count_longitudinal_cracks', 0),
            data.get('count_transverse_cracks', 0),
            data.get('count_alligator_cracks', 0),
            data.get('count_potholes', 0),
            inspection_id
        )

        print("Prepared Query:", query)
        print("Values:", values)

        # Eksekusi query dengan exception handling
        try:
            cursor.execute(query, values)
            conn.commit()
            if cursor.rowcount > 0:
                status = True  # Update berhasil
            else:
                print("No rows updated. Check if the ID exists.")
        except Exception as e:
            print("Database update error:", e)
            conn.rollback()  # Rollback jika terjadi kesalahan
        finally:
            conn.close()
    else:
        print("Failed to connect to the database.")

    return status


def create_inspection(location):
    status = False
    conn = connect_to_database()
    if conn:
        cursor = conn.cursor()
        columns = "{0}, {1}, {2}, {3}, {4}, {5}".format(
            "location",
            "count_crack",
            "count_longitudinal_cracks",
            "count_transverse_cracks",
            "count_alligator_cracks",
            "count_potholes"
        )
        values = '"{0}", {1}, {2}, {3}, {4}, {5}'.format(
            location,
            0,
            0,
            0,
            0,
            0,
            0
        )
        query = "INSERT INTO Inspections ({0}) VALUES ({1})".format(columns, values)
        try:
            cursor.execute(query)
            conn.commit()
            inspection_id = cursor.lastrowid
            status = inspection_id
        except Exception as e:
            conn.rollback()  # Rollback jika terjadi kesalahan
        finally:
            conn.close()
    return status


def save_mapping(locations, output_file="location.gpx"):
    # Membuat objek GPX
    gpx = gpxpy.gpx.GPX()

    for lat, lon in locations:
        waypoint = gpxpy.gpx.GPXWaypoint(latitude=lat, longitude=lon)
        gpx.waypoints.append(waypoint)

    # Menyimpan ke file GPX
    with open(output_file, "w") as file:
        file.write(gpx.to_xml())

    print(f"Lokasi GPS telah disimpan ke {output_file}")


def update_mapping(locations, output_file="location.gpx"):
    # Coba membuka file GPX yang ada
    try:
        with open(output_file, "r") as file:
            gpx = gpxpy.parse(file)
    except FileNotFoundError:
        # Jika file tidak ada, buat objek GPX baru
        gpx = gpxpy.gpx.GPX()

    # Menambahkan setiap lokasi ke GPX
    for lat, lon in locations:
        waypoint = gpxpy.gpx.GPXWaypoint(latitude=lat, longitude=lon)
        gpx.waypoints.append(waypoint)

    # Menyimpan kembali ke file GPX
    with open(output_file, "w") as file:
        file.write(gpx.to_xml())

    print(f"Beberapa lokasi GPS telah ditambahkan ke {output_file}")

# def get_items():
#     cursor.execute('SELECT * FROM items')
#     items = cursor.fetchall()
#     conn.close()
#     item_list = [{'id': item[0], 'name': item[1], 'price': item[2]} for item in items]
#     return jsonify({'items': item_list})
#
#
# def get_item(item_id):
#     cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
#     item = cursor.fetchone()
#     conn.close()
#     if item:
#         return jsonify({'id': item[0], 'name': item[1], 'price': item[2]})
#     return jsonify({'message': 'Item not found'}, 404)
