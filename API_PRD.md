**Films Page**
- "rent out a film": needs PMT and FILM/STORE/CUST details
    - REQUIREMENTS
        - create new rental record with return_date=NULL
        - create new payment record

- View customer rental records
    - f(customer_id, store_id) -> Map[("outgoing_rentals", "past_rentals") -> List[Rental]]
- Returned a rented movie
    - f(rental_id)
