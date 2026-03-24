from app.models.booking_logs import BookingLog

def log_booking(db, match_id, seat_no, user_id, status, price=None):
    log = BookingLog(
        match_id=match_id,
        seat_no=seat_no,
        user_id=user_id,
        status=status,
        price=price
    )
    db.add(log)
    db.commit()