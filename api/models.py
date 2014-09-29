# Database Model
import flaskr

class Order(flaskr.db.Model):
    __tablename__ =  'orders'

    id = flaskr.db.Column(flaskr.db.Integer, primary_key=True, autoincrement=False)
    name = flaskr.db.Column(flaskr.db.String(120))
    email = flaskr.db.Column(flaskr.db.String(120), nullable=True)
    birthday = flaskr.db.Column(flaskr.db.Date, nullable=True)
    state = flaskr.db.Column(flaskr.db.String(2), nullable=True)
    zipcode = flaskr.db.Column(flaskr.db.String(9), nullable=True)

    valid = flaskr.db.Column(flaskr.db.Boolean, default=True)
    errors = flaskr.db.Column(flaskr.db.Text, nullable=True)

    def __init__(self, *args, **kwargs):
        for field in kwargs:
            setattr(self, field, kwargs[field])

    def __repr__(self):
        return '<Order %d>' % self.id