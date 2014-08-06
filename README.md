# API

## Server

Server is located on https://empatika-resto.appspot.com/.

## Endpoints

### Venues list for current company

GET `/api/venues/<company_id>`

No parameters

```
#!js
{
    "venues": [
        {
           "venueId": venue_id,     // string
           "name": name,            // string
           "address": address,      // string
           "latitude": latitude,    // float
           "longitude": longitude,  // float
           "logoUrl": logo_url,     // string
           "phone": phone           // string
        },
        ...
    ]
}
```

### Menu for current venue

GET `/api/venue/<venue_id>/menu`

No parameters

```
#!js
{
    "menu": [
        {
            "parent": parent group,                                 // ParentGroup
            "hasChildren": children for current group,              // boolean
            "image": [
                "imageUrl": url,                                    // string
                "uploadDate": date in format DD.MM.YYYY HH:MM:SS,   // string
                "imageId": image id,                                // string
            ],
            "id": id,                                               // string
            "products": [
                {
                    "code": code,                                   // string
                    "name": product name,                           // string
                    "weight": weight in kg,                         // float
                    "modifiers": [

                    ],
                    "images": [
                        <image_url>, ...
                    ],
                    "productId": product id,                        // string
                    "description": description,                     // string

                }, ...
            ],
            "children": [
                <info like in "products">, ...
            ],
            "name": name                                            // string
        },
        ...
    ]
}
```

### Get history for company

GET `/api/history`

Parameters:

* `client_id (int)`
* `organisation_id (string)`

```
#!js
{
    "history": {
        "venueId": venue_id,                    // string
        "address": address,                     // string
        "name": name,                           // string
        "local_history": [
            "self": isSelfService,              // string
            "order_id": orderId,                // string
            "order_number": number,             // string
            "order_adress": address,            // string
            "order_deliver_date": date,         // string
            "order_current_date": current_time, // string
            "order_phone": phone,               // string
            "order_discount": discount,         // string
            "order_total": sum,                 // string
            "order_items": [
                "item_sum": sum,                // string
                "item_amount": amount,          // string
                "item_title": name              // string
            ]
        ]
    }
}
```

### Get key by address

GET `/api/address`

Parameters:

* `address (string)`

```
#!js
[
    "key": key,                 // string
    "source": "google",
    "title": title,             // string
    "description": description, // string
]
```

### Get location by key

GET `/api/get_info`

Parameters:

* `key (string)`

```
#!js
{
    "address": address,         // string
    "location": location,       // string
}
```

### Get delivery info

GET `/api/check_delivery`

### Create new order

POST `/api/venue/<venue_id>/order/new`

Parameters:

* `name (string)`
* `phone (string)`
* `customer_id (string)`
* `deliveryType (string)`
* `sum (string)`
* `date (string)`
* `items (json)`

```
#!js
{
    "customerId": customer_id,         // string
    "order": [
        "orderId": order_id,           // string
        "number": number,              // string
        "status": status,              // int
        "sum": sum,                    // float
        "items": items,                // json
        "venueId": venue_id,           // string
    ]
}
```

### Change state flag

GET `/api/venue/<venue_id>/order/<order_id>`

No parameters

```
#!js
{
    "order": [
        "orderId": order_id,                                                    // string
        "number": number,                                                       // string
        "status": status ("Новая" -> "Подтвержден"), ("Закрыта" -> "Закрыт"),   // int
        "sum": sum,                                                             // float
        "items": items,                                                         // json
        "venueId": venue_id,                                                    // string
    ]
}
```

### Get new state

GET `/api/order/<order_id>`

No parameters

```
#!js
{
    "order": [
        "orderId": order_id, // string
        "number": number,    // string
        "status": status,    // int
        "sum": sum,          // float
        "items": items,      // json
        "venueId": venue_id, // string
    ]
}
```

### Get new state

POST `/api/status`

Parameters:

* `json (json)`

```
#!js
{
    "orders": [
        "order_id": order_id, // string
        "name": name,         // string
        "status": status,     // int
        "address": address,   // string
        "venue_id": venue_id, // string
        "createdTime": time,  // string
    ]
}
```

### Add new company

POST `/api/add_company`

Parameters:

* `name (string)`
* `password (string)`

```
#!js
{
    "organization_id": organization_id, // int
}
```

### Add new payment type

POST `/api/payment_type/add`

Parameters:

* `name (string)`
* `venue_id (string)`
* `type_id (int)`
* `iiko_uuid (string)`
* `available (bool)`

```
#!js
{
    "venue_id": venue_id,   // string
    "payment_type": type_id // int
}
```

### Edit payment type

POST `/api/payment_type/edit`

Parameters:

* `name (string)`
* `type_id (int)`
* `iiko_uuid (string)`
* `available (bool)`

```
#!js
{
    "error": error,     // string
    "code": status code // int
}
```

### Get payment types

GET `/api/payment_type/<venue_id>`

No parameters

```
#!js
{
    "types": [
        "type_id": type_id,     // int
        "name": name,           // string
        "iiko_uuid": iiko_uuid, // string
        "available": available  // bool
    ]
}
```

### Get delivery types

GET `/api/delivery_types`

Parameters:

* `organization_id (string)`

```
#!js
{
    "types": [
        "type_id": type_id,     // int
        "name": name,           // string
        "available": available  // bool
    ]
}
```

### Add new delivery type

POST `/api/delivery_type/add`

Parameters:

* `organization_id (string)`
* `venue_id (string)`
* `type_id (int)`
* `available (bool)`

```
#!js
{
    "venue_id": venue_id,   // string
    "payment_type": type_id // int
}
```

### Registration of order

GET `/api/alfa/registration`

Parameters:

* `client_id (string)`
* `amount (int) -> optional`

```
#!js
{
    "fromUrl": url,         // string
    "orderId": alfabank id  // string
}
```

### Get binding id

GET `/api/alfa/binding`

Parameters:

* `orderId (string)`

```
#!js
{
    "id": binding id        // string
}
```

### Create order (1st stage)

GET `/api/alfa/create`

Parameters:

* `order_id (string)`
* `binding_id (string)`

```
#!js
{
    "code": code        // string
}
```

### Pay order (2nd stage)

GET `/api/alfa/pay`

Parameters:

* `order_id (string)`
* `amount (int) -> optional (default: 0 (all sum))`

```
#!js
{
    "code": code        // string
}
```

### Reset order

GET `/api/alfa/reset`

Parameters:

* `order_id (string)`

```
#!js
{
    "code": code        // string
}
```

### Unbind card

GET `/api/alfa/unbind`

Parameters:

* `binding_id (string)`

```
#!js
{
    "code": code        // string
}
```