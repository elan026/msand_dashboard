import os, cv2, numpy as np
from flask import Flask, request, render_template, url_for, jsonify, send_from_directory
from utils.db import db, Submission
from utils.image_processing import save_image_file, analyze_image
from utils import calc, psd_from_image, psd_stats, density, silt_estimate

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def create_app():
    app = Flask(__name__)
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database', 'data.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    db.init_app(app)

    @app.before_first_request
    def create_tables():
        db.create_all()

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/upload', methods=['POST'])
    def upload():
        device_id = request.form.get('device_id', 'web-client')
        temp = request.form.get('temp', None)
        humidity = request.form.get('humidity', None)
        moisture = request.form.get('moisture', None)
        file = request.files.get('image')
        if file is None:
            return jsonify({"success": False, "error": "No image attached"}), 400

        saved_path = save_image_file(file, app.config['UPLOAD_FOLDER'])
        analyze_result = analyze_image(saved_path, app.config['UPLOAD_FOLDER'])
        vision_conf = analyze_result.get('vision_conf', 0.0)

        # parse advanced fields
        try:
            moisture_adc = request.form.get('moisture_adc', None)
            turbidity_adc = request.form.get('turbidity_adc', None)
            weight_g = float(request.form.get('weight_g', 0) or 0)
            container_vol_ml = float(request.form.get('container_volume_ml', 1000) or 1000)
            displaced_ml = float(request.form.get('displaced_volume_ml', 0) or 0)
            jar_settled_mm = float(request.form.get('jar_settled_mm', 0) or 0)
            jar_total_mm = float(request.form.get('jar_total_mm', 0) or 0)
            scale_px = float(request.form.get('scale_marker_px', 50) or 50)
            scale_mm = float(request.form.get('scale_marker_mm', 30) or 30)
        except Exception as e:
            return jsonify({"success": False, "error": "Invalid numeric input", "detail": str(e)}), 400

        # image PSD
        img = cv2.imdecode(np.fromfile(saved_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        pixels_to_mm = calc.pixel_to_mm_scale(scale_px, scale_mm)
        diameters_mm = psd_from_image.estimate_particle_sizes(img, pixels_to_mm)
        psd_summary = psd_stats.compute_psd_and_fm(diameters_mm)

        # bulk and sg
        bulk = density.compute_bulk_density(weight_g, container_vol_ml) if weight_g>0 else None
        sg = density.compute_specific_gravity_particle(weight_g, displaced_ml) if displaced_ml>0 else None
        silt_percent = silt_estimate.silt_fraction_from_settled_height(jar_settled_mm, jar_total_mm)

        # moisture percent simple mapping if available
        def moisture_from_adc(adc):
            try:
                a,b = -0.02, 100.0
                return max(0.0, min(100.0, a*float(adc) + b))
            except:
                return None
        moisture_percent = moisture_from_adc(moisture_adc) if moisture_adc else (float(moisture) if moisture else None)

        # fused score (simple)
        fused_score = 0.7*vision_conf
        if moisture_percent is not None:
            fused_score = 0.7*vision_conf + 0.3*(1 - min(moisture_percent/60.0,1.0))
        label = "Inferior"
        if fused_score > 0.75:
            label = "Superior"
        elif fused_score > 0.5:
            label = "Moderate"

        # persist
        sub = Submission(
            device_id=device_id,
            image_path=saved_path,
            segmented_path=analyze_result.get('segmented_path'),
            label=label,
            confidence=float(fused_score),
            vision_conf=float(vision_conf),
            temp=float(temp) if temp else None,
            humidity=float(humidity) if humidity else None,
            moisture=moisture_percent
        )
        db.session.add(sub)
        db.session.commit()

        resp = {
            "success": True,
            "label": label,
            "confidence": fused_score,
            "vision_conf": vision_conf,
            "segmented_url": url_for('static', filename=f"uploads/{os.path.basename(analyze_result.get('segmented_path'))}", _external=True),
            "psd": psd_summary,
            "bulk_density": bulk,
            "specific_gravity": sg,
            "silt_percent": silt_percent,
            "moisture_percent": moisture_percent
        }
        return jsonify(resp)

    @app.route('/sensor', methods=['POST'])
    def receive_sensor_data():
        data = request.get_json()
        # For demo: just print and return ok; production should store in DB and link with sample_id
        print("Received sensor data:", data)
        return jsonify({"status":"success","received":data})

    @app.route('/dashboard')
    def dashboard():
        q = Submission.query.order_by(Submission.created_at.desc()).limit(200).all()
        return render_template('dashboard.html', submissions=q)

    @app.route('/export/csv')
    def export_csv():
        import csv
        subs = Submission.query.all()
        csv_path = os.path.join('database', 'export.csv')
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id','device_id','image_path','segmented_path','label','confidence','vision_conf','temp','humidity','moisture','created_at'])
            for s in subs:
                writer.writerow([s.id, s.device_id, s.image_path, s.segmented_path, s.label, s.confidence, s.vision_conf, s.temp, s.humidity, s.moisture, s.created_at])
        return send_from_directory('database', 'export.csv', as_attachment=True)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)