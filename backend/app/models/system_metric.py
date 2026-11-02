from app.extensions import db


class SystemMetric(db.Model):
    __tablename__ = "system_metrics"

    id = db.Column(db.Integer, primary_key=True)

    cpu = db.Column(db.Float)

    memory = db.Column(db.Float)

    disk = db.Column(db.Float)

    network = db.Column(db.Float)

    timestamp = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def __repr__(self):
        return f"<Metric {self.timestamp}>"