from sqlalchemy.orm import Session
from app.models.match import Match
from app.models.seat import Seat


def create_match_with_seats(
    db: Session,
    team1: str,
    team2: str,
    stadium: str,
    date: str,
    total_seats: int = 50
):
    match = Match(
        team1=team1,
        team2=team2,
        stadium=stadium,
        date=date,
        total_seats=total_seats,
        available_seats=total_seats
    )

    db.add(match)
    db.commit()
    db.refresh(match)

    # Generate seats
    seats = []
    rows = ["A", "B", "C", "D", "E"]

    seat_count = 0
    for row in rows:
        for num in range(1, 11):
            if seat_count >= total_seats:
                break

            seat = Seat(
                match_id=match.id,
                seat_number=f"{row}{num}",
                is_booked=False
            )
            seats.append(seat)
            seat_count += 1

        if seat_count >= total_seats:
            break

    db.add_all(seats)
    db.commit()

    return {
        "message": "Match created with seats",
        "match_id": match.id
    }