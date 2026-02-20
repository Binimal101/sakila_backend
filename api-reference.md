**Universal Error Codes:**

    1) 200: Successful request
    2) -100: Endpoint missing required parameters

***GET /api/health***


***POST api/top_5_rentals ***

    Params:
        1) store_id:store_id

    Returns:
        {
            <Film>, 
            <Film>, 
            ..., 
            <Film>
        }

    Status Codes:
        1) -1: store does not exist

***POST /api/details/film***

    Params:
        1) film_id:film_id

    Returns:
        {
            "film": <Film>
        }

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

***POST /api/query/films***

    Params:
        1) filter_var:ENUM("name", "genre", "actor") [OPTIONAL]
        2) filter_content:filter_content [OPTIONAL]
        3) top_n:top_n (n) = 5 [OPTIONAL]

    Returns:
        {
            "1": <Film>
            "2": <Film>
            ...
            "n": <Film>
        }

***POST /api/rent***

    Params:
        1) store_id:store_id
        2) film_id:film_id
        3) customer_id:customer_id
        4) staff_id:staff_id
    
    Returns:
        {
            "rental_id":rental_id
        }
    
    Status codes:
        1) -1: Store does not exist
        2) -2: film does not exist
        3) -3: customer does not exist
        4) -4: staff does not exist

***POST /api/query/customer***

    Params:
        1) filter_var:ENUM("first_name", "last_name", "customer_id") [OPTIONAL]
        2) filter_value:filter_value (string for names, int for customer_id) [OPTIONAL]
        3) offset:offset (o) = 0 [OPTIONAL]
        4) top_n:top_n (n) = 20 [OPTIONAL]

    Returns:
        {
            "customers": List[Customer]
        }

***POST /api/customer/create***
    
    Params:
        1) store_id:store_id
        2) first_name:first_name
        3) last_name:last_name
        4) email:email [OPTIONAL]
        5) phone_number:phone_number
        6) address: {
            address_line1:address_line1,
            address_line2:address_line2 [OPTIONAL],
            district:district,
            city:city,
            country:country,
            postal_code:postal_code [OPTIONAL],
        }
    
    Returns:
        {
            customer_id:customer_id
        }
    
    Status codes:
        1) -1: Store does not exist
        2) -2: first name format invalid
        3) -3: last name format invalid
        4) -4: email format invalid
        5) -5: phone number format invalid (talk to matt)
        6) -6: geocoding error / invalid address

***POST /api/customer/edit***
    
    Params:
        1) store_id:store_id
        2) first_name:first_name
        3) last_name:last_name
        4) email:email [OPTIONAL]
        5) phone_number:phone_number
        6) address: {
            address_line1:address_line1,
            address_line2:address_line2 [OPTIONAL],
            district:district,
            city:city,
            country:country,
            postal_code:postal_code [OPTIONAL],
        }
        7) customer_id:customer_id
    
    Status codes:
        1) -1: Store does not exist
        2) -2: first name format invalid
        3) -3: last name format invalid
        4) -4: email format invalid
        5) -5: phone number format invalid (talk to matt)
        6) -6: geocoding error / invalid address
        7) -7: customer does not exist at this store

***POST /api/customer/delete***

    Params:
        1) customer_id
        2) store_id
    
    Status codes:
        1) -1: customer does not exist at store
        2) -2: store does not exist

***POST /api/details/customer***
    
    Notes:
        Will return rental records for store having store_id

    Params:
        1) store_id
        2) customer_id
    
    Returns:
        {
            "customer": <Customer>
            "rental_history": List[Rental]
            "outgoing_rentals": List[Rental]
        }


    Status codes:
        1) -1: store does not exist
        2) -2: customer does not exist at this store

***POST /api/return***

    Params:
        1) rental_id:rental_id
    
    Status codes:
        1) rental does not exist