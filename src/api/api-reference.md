**Universal Error Codes:**

    1) 200: Successful request



*** GET api/top_5_rentals ***

    Params:
        1) store_id

    Returns:
        {
            "1": <Rental>, 
            "2": <Rental>, 
            ..., 
            "5": <Rental>
        }

    Status Codes:
        1) -1: store does not exist


***GET /api/film_details***

    Params:
        1) film_id

    Returns:
        <Film>

    Status Codes:
        1) -1: Film does not exist
    

***GET top_5_actors***

    Params:
        1) store_id

    Returns:
        {
            "1": <Actor>.
            "2": <Actor>.
            ...
            "5": <Actor>
        }

    Status Codes:
        1) -1: Store does not exist

*** GET api/top_n_rentals_with_actor***

    Notes:
        This aggregates rentals from this actor that appear at ANY store

    Params:
        1) actor_id
        2) offset (o) = 0 [OPTIONAL]
        3) top_n (n) = 50 [OPTIONAL]

    Returns:
        {
            "o": <Rental>, 
            "o+1": <Rental>, 
            ..., 
            "n": <Rental>
        }

    Status Codes:
        1) -1: store does not exist