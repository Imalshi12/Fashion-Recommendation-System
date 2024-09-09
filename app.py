from flask import Flask, render_template, request
import pickle
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure the MySQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/body_shape_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define a model for the predictions
class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dress_size = db.Column(db.Float, nullable=False)
    breasts = db.Column(db.Float, nullable=False)
    waist = db.Column(db.Float, nullable=False)
    hips = db.Column(db.Float, nullable=False)
    shoe = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    body_shape = db.Column(db.String(50), nullable=False)

# Load the model
model = pickle.load(open('best_model.pkl', 'rb'))

@app.route('/')
def home():
    result = ''
    return render_template('index.html', result=result)

@app.route('/predict', methods=['POST'])
def predict():
    # Get input values from the form
    dress_size = float(request.form['Dress_size'])
    breasts = float(request.form['Breasts'])
    waist = float(request.form['Waist'])
    hips = float(request.form['Hips'])
    shoe = float(request.form['Shoe'])
    height = float(request.form['Height'])
    weight = float(request.form['Weight'])

    print(f"Received data: {dress_size}, {breasts}, {waist}, {hips}, {shoe}, {height}, {weight}")
    
    # Make prediction
    features = [[dress_size, breasts, waist, hips, shoe, height, weight]]
    result = model.predict(features)[0]
    
    # Map the result to body shapes
    body_shapes = ['Banana', 'Hourglass', 'Pear', 'Apple', 'Inverted Triangle', 'Rectangle']
    body_shape_result = body_shapes[result]
    
    # Save to the database
    prediction = Prediction(dress_size=dress_size, breasts=breasts, waist=waist, hips=hips,
                            shoe=shoe, height=height, weight=weight, body_shape=body_shape_result)
    db.session.add(prediction)
    try:
        db.session.commit()
        print("Data successfully saved to the database.")
    except Exception as e:
        print(f"Error saving data: {e}")
        db.session.rollback()

    return render_template('index.html', result=body_shape_result)

@app.route('/predictions')
def predictions():
    all_predictions = Prediction.query.all()
    return render_template('predictions.html', predictions=all_predictions)

if __name__ == '__main__':
    with app.app_context():
        # Create the database and tables if they don't exist
        db.create_all()
    app.run(debug=True)