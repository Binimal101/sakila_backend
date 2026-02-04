**Universal Error Codes:**

    1) 200: Successful request

***GET /api/health***


***POST api/top_5_rentals ***

    Params:
        1) store_id:store_id

    Returns:
        {
            "1": <Rental>, 
            "2": <Rental>, 
            ..., 
            "5": <Rental>
        }

    Status Codes:
        1) -1: store does not exist


***POST /api/film_details***

    Params:
        1) film_id:film_id

    Returns:
        <Film>

    Status Codes:
        1) -1: Film does not exist
    

***POST /api/top_5_actors***

    Params:
        1) store_id:store_id

    Returns:
        {
            "1": <Actor>.
            "2": <Actor>.
            ...
            "5": <Actor>
        }

    Status Codes:
        1) -1: Store does not exist

***POST /api/top_n_rentals_with_actor***

    Notes:
        This aggregates rentals from this actor that appear at ANY store

    Params:
        1) actor_id:actor_id
        2) offset:offset (o) = 0 [OPTIONAL]
        3) top_n:top_n (n) = 50 [OPTIONAL]

    Returns:
        {
            "o": <Rental>, 
            "o+1": <Rental>, 
            ..., 
            "n": <Rental>
        }

    Status Codes:
        1) -1: Actor does not exist

***POST /api/query_films***

    Params:
        1) filter_var:ENUM("name", "genre", "actor")
        2) filter_content:filter_content
        3) top_n:top_n (n) = 5 [OPTIONAL]

    Returns:
        {
            "1": <Film>
            "2": <Film>
            ...
            "n": <Film>
        }

***POST /api/rent_film***

    Params:
        1) store_id:store_id
        2) film_id:film_id
        3) customer_id:customer_id
        4) staff_id:staff_id
    
    Returns:
        rental_id:rental_id

    
***POST /api/get_all_customers_at_store***